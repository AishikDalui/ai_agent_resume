import "./globals.css";
import Script from "next/script";

export const metadata = {
  title: "Aishik Dalui — Data Analyst Portfolio",
  description: "Aishik Dalui's interactive data analyst portfolio with AI-powered chat, session booking, and project showcase.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        {children}
        <Script
          src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"
          strategy="beforeInteractive"
        />
      </body>
    </html>
  );
}
