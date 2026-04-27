import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Attendance App Web",
  description: "Next.js + TypeScript runtime check page",
};

type RootLayoutProps = {
  children: ReactNode;
};

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="ko">
      <body style={{ fontFamily: "sans-serif", margin: 24 }}>{children}</body>
    </html>
  );
}
