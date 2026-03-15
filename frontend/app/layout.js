import "./globals.css";

export const metadata = {
  title: "Aishik Dalui Portfolio",
  description: "Portfolio, AI chat, booking, and admin tools for Aishik Dalui.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
