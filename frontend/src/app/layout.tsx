import type { Metadata } from "next";
import { Noto_Sans_JP } from "next/font/google";
import "./globals.css";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";
import { DisclaimerBanner } from "@/components/layout/disclaimer-banner";
import { QueryProvider } from "@/components/providers/query-provider";

const notoSansJP = Noto_Sans_JP({
  subsets: ["latin"],
  variable: "--font-noto-sans-jp",
  display: "swap",
});

export const metadata: Metadata = {
  title: "AI ポートフォリオアドバイザー",
  description:
    "あなたのリスク許容度に合わせた最適なポートフォリオをAIが提案します。日米の金融資産データに基づく教育目的の情報提供サービスです。",
  manifest: "/manifest.json",
  icons: [
    { url: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
    { url: "/icons/icon-512.png", sizes: "512x512", type: "image/png" },
  ],
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "PortAdvisor",
  },
  other: {
    "theme-color": "#0f172a",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja">
      <body className={`${notoSansJP.variable} font-sans antialiased`}>
        <QueryProvider>
          <div className="flex min-h-screen flex-col">
            <DisclaimerBanner />
            <Header />
            <main className="flex-1">{children}</main>
            <Footer />
          </div>
        </QueryProvider>
      </body>
    </html>
  );
}
