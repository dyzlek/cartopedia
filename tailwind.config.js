/** Tokens de DESIGN.md (thème brutaliste) */
module.exports = {
  content: ['./app/templates/**/*.html', './app/static/js/**/*.js'],
  theme: {
    borderRadius: { none: '0' },
    extend: {
      colors: {
        paper: '#F4F0E6',
        ink: '#000000',
        signal: '#FFE500',
        brut: '#FF3B30',
        volt: '#2B3BFF',
        acid: '#3DDC84',
        shock: '#FF6AD5',
        stone: '#D9D5C8',
        muted: '#595447',
      },
      boxShadow: {
        hard: '6px 6px 0 rgba(0,0,0,.3)',
        'hard-sm': '4px 4px 0 rgba(0,0,0,.3)',
        'hard-lg': '12px 12px 0 rgba(0,0,0,.3)',
      },
      borderWidth: { 3: '3px' },
      fontFamily: {
        display: ['"Archivo Black"', 'Impact', 'sans-serif'],
        sans: ['"Space Grotesk"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      keyframes: {
        reveal: {
          '0%': { transform: 'translateY(16px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
      animation: { reveal: 'reveal 240ms steps(4, end) both' },
    },
  },
  plugins: [],
};
