import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const githubPagesBridge = `
(() => {
  const base = location.pathname === "/musical-portal" || location.pathname.startsWith("/musical-portal/")
    ? "/musical-portal"
    : "";
  if (!base) return;

  const originalFetch = window.fetch.bind(window);
  window.fetch = (input, init) => {
    if (typeof input === "string" && input.startsWith("/") && !input.startsWith(base + "/")) {
      input = base + input;
    }
    return originalFetch(input, init);
  };

  document.addEventListener("click", (event) => {
    const anchor = event.target instanceof Element ? event.target.closest("a") : null;
    const href = anchor?.getAttribute("href");
    if (!href || !href.startsWith("/")) return;
    if (href.includes("?")) {
      event.preventDefault();
      location.href = href.startsWith(base + "/") ? href : base + href;
      return;
    }
    if (href.startsWith(base + "/")) return;
    event.preventDefault();
    location.href = base + href;
  }, true);
})();
`;

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "درگاه موزیکال — علیرضا کاوه",
  description: "پایگاه پژوهشی گونهٔ موزیکال سینمایی؛ فیلم‌ها، سبک‌های موسیقایی، عوامل و شماره‌های موزیکال.",
  other: {
    "codex-preview": "development",
  },
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fa" dir="rtl">
      <head>
        <script dangerouslySetInnerHTML={{ __html: githubPagesBridge }} />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
