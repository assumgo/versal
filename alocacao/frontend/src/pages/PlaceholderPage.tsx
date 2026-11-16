type PlaceholderPageProps = {
  title: string;
  description: string;
  features: { title: string; text: string }[];
};

export function PlaceholderPage({ title, description, features }: PlaceholderPageProps) {
  return (
    <section className="placeholder-page">
      <header className="page-header">
        <span className="eyebrow">Em construção</span>
        <h1>{title}</h1>
        <p>{description}</p>
      </header>
      <div className="placeholder-grid">
        {features.map((feature) => (
          <article key={feature.title} className="card-panel feature-card">
            <h3>{feature.title}</h3>
            <p>{feature.text}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
