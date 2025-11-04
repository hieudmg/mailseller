type PageHeaderProps = {
  title: string;
  subtitle?: string;
};

export function PageHeader({ title, subtitle }: PageHeaderProps) {
  return (
    <div className="mb-10 text-center">
      <h1 className="shadow-foreground gradient-text mb-6 pb-2 text-4xl text-transparent md:text-5xl">{title}</h1>
      {subtitle && <p className="mx-auto max-w-2xl text-xl text-slate-300">{subtitle}</p>}
    </div>
  );
}
