import Script from "next/script";

import { indexMarkup } from "../app_components/legacyMarkup";

export default function HomePage() {
  return (
    <>
      <div dangerouslySetInnerHTML={{ __html: indexMarkup }} />
      <Script src="/app.js" strategy="afterInteractive" />
    </>
  );
}
