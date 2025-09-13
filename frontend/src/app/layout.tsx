import { UserProvider } from '@auth0/nextjs-auth0/client';
import { Toaster } from 'sonner';
import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Multi-Device Authentication',
  description: 'Secure multi-device authentication system with Auth0 integration',
  keywords: 'authentication, multi-device, Auth0, security',
  authors: [{ name: 'Your Company' }],
  viewport: 'width=device-width, initial-scale=1',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full">
      <body className="h-full bg-gray-50 antialiased">
        <UserProvider>
          <main className="min-h-full">
            {children}
          </main>
          <Toaster 
            position="top-right"
            expand={true}
            richColors
            closeButton
          />
        </UserProvider>
      </body>
    </html>
  );
}