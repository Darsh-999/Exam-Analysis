// Every chart on this screen surfaces its own API-provided title +
// description rather than a hand-written caption (see FRONTEND_DESIGN.md
// §6.1) - this wrapper is just that small header plus an optional toggle
// (e.g. the Count/Marks switch) on the right.
export default function ChartPanel({ title, description, toggle, children }) {
  return (
    <div>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-text-primary">{title}</h3>
          {description && <p className="mt-0.5 max-w-2xl text-xs text-text-muted">{description}</p>}
        </div>
        {toggle}
      </div>
      <div className="mt-4">{children}</div>
    </div>
  );
}
