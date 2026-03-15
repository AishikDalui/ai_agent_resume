import Script from "next/script";

import { adminMarkup } from "../../app_components/legacyMarkup";

export const metadata = {
  title: "Admin Dashboard",
};

export default function AdminPage() {
  return (
    <>
      <div dangerouslySetInnerHTML={{ __html: adminMarkup }} />
      <Script src="/admin.js" strategy="afterInteractive" />
    </>
  );
}
