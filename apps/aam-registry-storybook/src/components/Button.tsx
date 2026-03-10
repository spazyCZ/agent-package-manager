import React from 'react';

export interface ButtonProps {
  /** Button label */
  label: string;
  /** Visual variant */
  variant?: 'primary' | 'secondary' | 'danger';
  /** Optional click handler */
  onClick?: () => void;
  /** Disabled state */
  disabled?: boolean;
}

const variantClasses: Record<NonNullable<ButtonProps['variant']>, string> = {
  primary: 'bg-blue-600 hover:bg-blue-700 text-white',
  secondary: 'bg-gray-100 hover:bg-gray-200 text-gray-800 border border-gray-300',
  danger: 'bg-red-600 hover:bg-red-700 text-white',
};

/**
 * Reusable Button component for AAM Registry UI.
 */
export function Button({
  label,
  variant = 'primary',
  onClick,
  disabled = false,
}: ButtonProps): React.ReactElement {
  return (
    <button
      type="button"
      className={[
        'inline-flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed',
        variantClasses[variant],
      ].join(' ')}
      onClick={onClick}
      disabled={disabled}
    >
      {label}
    </button>
  );
}
