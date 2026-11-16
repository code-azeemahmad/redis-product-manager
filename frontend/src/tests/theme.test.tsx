import React, { act } from "react";
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { createRoot, Root } from "react-dom/client";
import { ThemeProvider, useTheme } from "../context/ThemeContext";

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;

const TestThemeComponent: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  return (
    <div>
      <span id="current-theme">{theme}</span>
      <button id="toggle-btn" onClick={toggleTheme}>
        Toggle
      </button>
    </div>
  );
};

describe("ThemeContext & Theme Switcher", () => {
  let container: HTMLDivElement | null = null;
  let root: Root | null = null;
  let mockStore: Record<string, string> = {};

  beforeEach(() => {
    mockStore = {};
    const mockStorage = {
      getItem: (key: string) => mockStore[key] ?? null,
      setItem: (key: string, value: string) => {
        mockStore[key] = value;
      },
      removeItem: (key: string) => {
        delete mockStore[key];
      },
      clear: () => {
        mockStore = {};
      },
      length: 0,
      key: () => null,
    };
    Object.defineProperty(window, "localStorage", {
      value: mockStorage,
      writable: true,
      configurable: true,
    });

    document.documentElement.removeAttribute("data-theme");
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);
  });

  afterEach(() => {
    if (root) {
      act(() => {
        root!.unmount();
      });
    }
    if (container && container.parentNode) {
      container.parentNode.removeChild(container);
    }
  });

  it("defaults to 'dark' theme when no preference is saved", () => {
    act(() => {
      root!.render(
        <ThemeProvider>
          <TestThemeComponent />
        </ThemeProvider>
      );
    });

    const themeEl = document.getElementById("current-theme");
    expect(themeEl?.textContent).toBe("dark");
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
    expect(mockStore["saas_theme"]).toBe("dark");
  });

  it("toggles from 'dark' to 'light' and updates attributes and localStorage", () => {
    act(() => {
      root!.render(
        <ThemeProvider>
          <TestThemeComponent />
        </ThemeProvider>
      );
    });

    const toggleBtn = document.getElementById("toggle-btn") as HTMLButtonElement;
    const themeEl = document.getElementById("current-theme");

    expect(themeEl?.textContent).toBe("dark");

    act(() => {
      toggleBtn.click();
    });

    expect(themeEl?.textContent).toBe("light");
    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
    expect(mockStore["saas_theme"]).toBe("light");

    // Toggle back to dark
    act(() => {
      toggleBtn.click();
    });

    expect(themeEl?.textContent).toBe("dark");
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
    expect(mockStore["saas_theme"]).toBe("dark");
  });

  it("respects saved 'light' preference from localStorage", () => {
    mockStore["saas_theme"] = "light";

    act(() => {
      root!.render(
        <ThemeProvider>
          <TestThemeComponent />
        </ThemeProvider>
      );
    });

    const themeEl = document.getElementById("current-theme");
    expect(themeEl?.textContent).toBe("light");
    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
  });
});
