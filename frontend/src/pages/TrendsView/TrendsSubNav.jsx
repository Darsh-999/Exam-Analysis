const SECTIONS = [
  { id: 'content-trends', label: 'Content Trends' },
  { id: 'papers', label: 'Papers' },
  { id: 'coverage', label: 'Coverage' },
  { id: 'exam-structure', label: 'Exam Structure' },
];

// Pure convenience navigation on top of a normal long page (no real
// routing) - smooth-scrolls to each section's anchor. Sticks just below the
// main TopNav (h-nav = 64px = top-16).
export default function TrendsSubNav() {
  function scrollToSection(id) {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  return (
    <div className="sticky top-16 z-30 -mx-6 mb-6 flex gap-1 border-b border-border bg-surface px-6 py-2 shadow-card sm:-mx-8 sm:px-8">
      {SECTIONS.map((section) => (
        <button
          key={section.id}
          type="button"
          onClick={() => scrollToSection(section.id)}
          className="rounded-btn px-3 py-1.5 text-sm font-medium text-text-secondary transition-colors hover:bg-background hover:text-text-primary"
        >
          {section.label}
        </button>
      ))}
    </div>
  );
}
