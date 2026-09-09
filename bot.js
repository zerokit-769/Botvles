import { Telegraf, Markup } from "telegraf";
import axios from "axios";
import dotenv from "dotenv";
import QRCode from "qrcode";

dotenv.config();

if (!process.env.BOT_TOKEN) {
    throw new Error("BOT_TOKEN is missing in .env");
}

if (!process.env.API_URL) {
    throw new Error("API_URL is missing in .env");
}

const bot = new Telegraf(process.env.BOT_TOKEN);

// =========================
// SERVER LIST
// =========================
const servers = [
    { label: "RI.RUXAD64.WORKERS.DEV", domain: "ri.ruxad64.workers.dev" }
];

// =========================
// REGION LIST
// =========================
const regions = [
    { code: "ID", label: "🇮🇩 Indonesia" },
    { code: "SG", label: "🇸🇬 Singapore" },
    { code: "MY", label: "🇲🇾 Malaysia" },
    { code: "JP", label: "🇯🇵 Japan" },
    { code: "US", label: "🇺🇸 USA" },
    { code: "KR", label: "🇰🇷 Korea" },
    { code: "FR", label: "🇫🇷 France" },
    { code: "TH", label: "🇹🇭 Thailand" },
    { code: "VN", label: "🇻🇳 Vietnam" }
];

// =========================
// SESSION
// =========================
const userSession = {};

// =========================
// KEYBOARD
// =========================
const mainMenu = Markup.keyboard([
    ["⚡ VLESS", "🔥 TROJAN", "🚀 VMESS"],
    ["🌐 PRJCTDEV"]
]).resize().persistent();

// =========================
// START
// =========================
bot.start(async (ctx) => {
    await ctx.reply("WELCOME TO VLESS BOT 🚀", mainMenu);
});

// =========================
// CLASH BUILDER (FIXED 100%)
// =========================
function buildClash(type, data) {

    const server = data.server || "ri.ruxad64.workers.dev";
    const label = data.label || server;
    const path = data.path || "/";

    // VLESS
    if (type === "vless") {
        return `
- name: ${label}
  server: ${server}
  port: 443
  type: vless
  uuid: ${data.uuid}
  cipher: auto
  tls: true
  skip-cert-verify: true
  servername: ${server}
  network: ws
  ws-opts:
    path: ${path}
    headers:
      Host: ${server}
  udp: true
`.trim();
    }

    // VMESS
    if (type === "vmess") {
        return `
- name: ${label}
  server: ${server}
  port: 443
  type: vmess
  uuid: ${data.uuid}
  alterId: 0
  cipher: auto
  tls: true
  skip-cert-verify: true
  servername: ${server}
  network: ws
  ws-opts:
    path: ${path}
    headers:
      Host: ${server}
  udp: true
`.trim();
    }

    // TROJAN
    if (type === "trojan") {
        return `
- name: ${label}
  server: ${server}
  port: 443
  type: trojan
  password: ${data.uuid}
  network: ws
  sni: ${server}
  skip-cert-verify: true
  ws-opts:
    path: ${path}
    headers:
      Host: ${server}
  udp: true
`.trim();
    }

    return "";
}

// =========================
// STEP 1 TYPE SELECT
// =========================
bot.hears(["⚡ VLESS", "🔥 TROJAN", "🚀 VMESS"], async (ctx) => {

    const type =
        ctx.message.text === "⚡ VLESS"
            ? "VLESS"
            : ctx.message.text === "🔥 TROJAN"
            ? "TROJAN"
            : "VMESS";

    userSession[ctx.from.id] = { type };

    const serverButtons = servers.map((s) =>
        Markup.button.callback(s.label, `${type}_SERVER_${s.domain}`)
    );

    await ctx.reply(
        `🌐 Select Server for ${type}`,
        Markup.inlineKeyboard(serverButtons, { columns: 1 })
    );
});

// =========================
// STEP 2 SERVER SELECT
// =========================
["VLESS", "TROJAN", "VMESS"].forEach((type) => {
    servers.forEach((server) => {

        bot.action(`${type}_SERVER_${server.domain}`, async (ctx) => {
            await ctx.answerCbQuery();

            userSession[ctx.from.id] = {
                ...(userSession[ctx.from.id] || {}),
                type,
                server: server.domain,
                serverLabel: server.label
            };

            const regionButtons = regions.map((r) =>
                Markup.button.callback(
                    r.label,
                    `${type}_REGION_${server.domain}_${r.code}`
                )
            );

            await ctx.editMessageText(
                `🌍 Select Region\n📡 Server: ${server.domain}\n⚙️ Type: ${type}`,
                Markup.inlineKeyboard(regionButtons, { columns: 2 })
            );
        });

    });
});

// =========================
// STEP 3 REGION SELECT + GENERATE
// =========================
["VLESS", "TROJAN", "VMESS"].forEach((type) => {
    servers.forEach((server) => {
        regions.forEach((region) => {

            bot.action(`${type}_REGION_${server.domain}_${region.code}`, async (ctx) => {

                try {
                    await ctx.answerCbQuery();

                    const userId = ctx.from.id;

                    const session = userSession[userId] || {};

                    await ctx.editMessageText(
                        `⏳ Creating ${type} Account...\n🌍 ${region.label}\n📡 Server: ${server.domain}`
                    );

                    const response = await axios.post(
                        `${process.env.API_URL.replace(/\/$/, "")}/api/generate`,
                        {
                            cc: region.code,
                            domain: server.domain,
                            proto: type.toLowerCase()
                        },
                        { timeout: 30000 }
                    );

                    const data = response.data ?? {};

                    // =========================
                    // FIX DATA (IMPORTANT)
                    // =========================
                    const fixedData = {
                        ...data,
                        server: server.domain,
                        label: `${server.label} ${region.label}`,
                        path: data.path || `/${region.code}`
                    };

                    const qrBuffer = await QRCode.toBuffer(
                        data[type.toLowerCase()] ?? data.vless ?? data.vmess ?? data.trojan ?? "",
                        { type: "png", width: 300 }
                    );

                    const clash = buildClash(type.toLowerCase(), fixedData);

                    await ctx.replyWithPhoto({ source: qrBuffer });

                    await ctx.reply(
`✅ ${type} ACCOUNT CREATED

🌍 Region : ${region.label}
🌐 Server : ${server.domain}
🆔 UUID : \`${data.uuid ?? "-"}\`
📂 Path : \`${fixedData.path}\`

━━━━━━━━━━━━━━━━━━━━━━

\`\`\`
${data[type.toLowerCase()] ?? "-"}
\`\`\`

━━━━━━━━━━━━━━━━━━━━━━

📦 CLASH CONFIG (YAML)

\`\`\`
${clash}
\`\`\`
`,
                        {
                            parse_mode: "Markdown",
                            disable_web_page_preview: true
                        }
                    );

                } catch (err) {
                    console.error(err.message);
                    await ctx.reply("❌ Failed to create account.");
                }
            });

        });
    });
});

// =========================
// PRJCTDEV LINK
// =========================
bot.hears("🌐 PRJCTDEV", async (ctx) => {
    await ctx.reply(
        "🔗 Open PRJCTDEV Website:",
        Markup.inlineKeyboard([
            Markup.button.url("PRJCTDEV", "https://prjctdev.my.id")
        ])
    );
});

// =========================
// START BOT
// =========================
bot.launch()
    .then(() => console.log("🤖 BOT RUNNING + FIXED CLASH YAML"))
    .catch(console.error);

// =========================
// STOP HANDLER
// =========================
process.once("SIGINT", () => bot.stop("SIGINT"));
process.once("SIGTERM", () => bot.stop("SIGTERM"));
