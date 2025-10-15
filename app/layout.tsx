import type { Metadata, Viewport } from "next";
import "./globals.css";
import { ToastProvider } from "@/components/ui";

export const metadata: Metadata = {
  title: "拆词鸭 - ChaiWord Duck",
  description: "专注于成人英语长单词学习的创新教育产品",
  keywords: ["英语学习", "单词记忆", "长单词", "词根拆解", "语言游戏"],
  authors: [{ name: "ChaiWord Duck Team" }],
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className="font-sans antialiased">
        <ToastProvider>
          {children}
        </ToastProvider>
      </body>
    </html>
  );
}
