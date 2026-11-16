import React from "react";
import { BrowserRouter, Link, Route, Routes } from "react-router-dom";
import { Navbar } from "./components/Navbar";
import { ThemeProvider } from "./context/ThemeContext";
import { CataloguePage } from "./pages/CataloguePage";
import { DashboardPage } from "./pages/DashboardPage";
import { ProductDetailPage } from "./pages/ProductDetailPage";

export const App: React.FC = () => {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <div className="app-container">
        <Navbar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<CataloguePage />} />
            <Route path="/products/:id" element={<ProductDetailPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route
              path="*"
              element={
                <div className="card" style={{ textAlign: "center", padding: "4rem 2rem", maxWidth: "600px", margin: "3rem auto" }}>
                  <h2 style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>404 — Page Not Found</h2>
                  <p style={{ color: "var(--color-steel)", margin: "1rem 0 1.5rem" }}>
                    The page you are looking for does not exist in this application.
                  </p>
                  <Link to="/" className="btn btn-primary">
                    Return to Catalogue
                  </Link>
                </div>
              }
            />
          </Routes>
        </main>

        {/* Footer */}
        <footer
          style={{
            backgroundColor: "var(--color-canvas)",
            borderTop: "1px solid var(--color-hairline-soft)",
            padding: "1.5rem 1.5rem",
            marginTop: "auto",
            textAlign: "center",
            fontSize: "13px",
            color: "var(--color-steel)",
          }}
        >
          <span>&copy; {new Date().getFullYear()} SaaS Product Manager. All rights reserved.</span>
        </footer>
      </div>
    </BrowserRouter>
  </ThemeProvider>
);
};

export default App;
