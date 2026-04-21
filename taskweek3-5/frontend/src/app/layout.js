import "./globals.css";

export const metadata = {
  title: "TLU Smart Tutor",
  description: "Academic AI Assistant",
};

export default function RootLayout({ children }) {
  return (
    <html lang="vi">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
