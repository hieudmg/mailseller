import { TopNavbar } from '@/components/top-navbar';

export default function PublicLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <>
      <TopNavbar />
      <main className="container mx-auto">{children}</main>
    </>
  );
}
