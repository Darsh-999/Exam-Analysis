const VARIANT_CLASSES = {
  primary:
    'bg-linear-to-r from-primary to-primary-amber text-white hover:brightness-105',
  secondary:
    'bg-surface border border-border text-text-primary hover:bg-background',
};

const SIZE_CLASSES = {
  default: 'h-10 px-4 text-sm',
  sm: 'h-8 px-3 text-xs',
};

// variant: 'primary' | 'secondary' — size: 'default' | 'sm'
export default function Button({
  variant = 'primary',
  size = 'default',
  className = '',
  children,
  ...rest
}) {
  return (
    <button
      type="button"
      className={`inline-flex items-center justify-center gap-2 rounded-btn font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 ${VARIANT_CLASSES[variant]} ${SIZE_CLASSES[size]} ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}
