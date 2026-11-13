import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider, useTheme } from '../theme/ThemeProvider';

function Probe() {
  const { theme, toggleTheme } = useTheme();
  return (
    <button type="button" onClick={toggleTheme}>
      {theme}
    </button>
  );
}

describe('ThemeProvider', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute('data-theme');
  });

  it('alterna entre claro e escuro e persiste em data-theme', async () => {
    const user = userEvent.setup();
    render(
      <ThemeProvider>
        <Probe />
      </ThemeProvider>,
    );

    const button = screen.getByRole('button');
    const initial = button.textContent;
    expect(document.documentElement.getAttribute('data-theme')).toBe(initial);

    await user.click(button);
    const next = initial === 'light' ? 'dark' : 'light';
    expect(button).toHaveTextContent(next);
    expect(document.documentElement.getAttribute('data-theme')).toBe(next);
  });
});
