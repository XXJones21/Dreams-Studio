import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Dreams Studio",
  description: "Describe a dream and watch it play out as a short film with sound.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
