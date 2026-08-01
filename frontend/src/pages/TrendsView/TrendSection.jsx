// muted: Coverage (§6.4) gets a slightly flatter background than the other
// sections - a visual cue that it's "is the data trustworthy" rather than
// "what does the exam test", so it shouldn't read with the same weight.
export default function TrendSection({ id, title, children, muted = false }) {
  return (
    <section
      id={id}
      className={`scroll-mt-28 rounded-card p-6 shadow-card ${
        muted ? 'border border-border bg-background' : 'bg-surface'
      }`}
    >
      <h2 className="mb-5 text-lg font-semibold text-text-primary">{title}</h2>
      <div className="space-y-8">{children}</div>
    </section>
  );
}
