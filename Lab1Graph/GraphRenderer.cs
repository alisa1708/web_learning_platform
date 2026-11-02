using System;
using System.Drawing;
using System.Drawing.Drawing2D;

namespace Lab1Graph
{
    public class GraphRenderer
    {
        public Color AxisColor { get; set; } = Color.Black;
        public Color CurveColor { get; set; } = Color.Red;
        public Color GridColor { get; set; } = Color.LightGray;
        public Color BackgroundColor { get; set; } = Color.White;
        public bool ShowGrid { get; set; } = true;
        public int Samples { get; set; } = 2000; 

        public void Draw(Graphics g, Rectangle area, Func<double, double> f,
                         double xMin, double xMax)
        {
            g.SmoothingMode = SmoothingMode.AntiAlias;

            using (var bg = new SolidBrush(BackgroundColor))
                g.FillRectangle(bg, area);

            int n = Samples;
            double[] xs = new double[n + 1];
            double[] ys = new double[n + 1];

            double yMin = double.PositiveInfinity;
            double yMax = double.NegativeInfinity;

            double dx = (xMax - xMin) / n;
            for (int i = 0; i <= n; i++)
            {
                double x = xMin + i * dx;
                double y = f(x);

                xs[i] = x;
                ys[i] = y;

                if (!double.IsNaN(y) && !double.IsInfinity(y))
                {
                    if (y < yMin) yMin = y;
                    if (y > yMax) yMax = y;
                }
            }

            if (double.IsInfinity(yMin) || double.IsInfinity(yMax))
                return; 

            if (Math.Abs(yMax - yMin) < 1e-12)
            {
                yMax += 1.0;
                yMin -= 1.0;
            }

            double MapX(double x) =>
                area.Left + (x - xMin) / (xMax - xMin) * area.Width;
            double MapY(double y) =>
                area.Bottom - (y - yMin) / (yMax - yMin) * area.Height;

            if (ShowGrid) DrawGridAndAxes(g, area, xMin, xMax, yMin, yMax, MapX, MapY);

            var oldClip = g.Clip;
            g.SetClip(area);

            try
            {
                using (var pen = new Pen(CurveColor, 2f))
                {
                    PointF? prev = null;
                    for (int i = 0; i <= n; i++)
                    {
                        double y = ys[i];

                        if (double.IsNaN(y) || double.IsInfinity(y))
                        {
                            prev = null;
                            continue;
                        }

                        var pt = new PointF((float)MapX(xs[i]), (float)MapY(y));

                        if (prev.HasValue)
                        {
                            g.DrawLine(pen, prev.Value, pt);
                        }
                        prev = pt;
                    }
                }
            }
            finally
            {
                g.Clip = oldClip;
            }
        }

        private void DrawGridAndAxes(Graphics g, Rectangle area,
            double xMin, double xMax, double yMin, double yMax,
            Func<double, double> mapX, Func<double, double> mapY)
        {
            using var gridPen = new Pen(GridColor, 1f) { DashStyle = DashStyle.Dot };
            using var axisPen = new Pen(AxisColor, 1.5f);

            double stepX = NiceStep((xMax - xMin) / 10.0);
            double stepY = NiceStep((yMax - yMin) / 8.0);

            using var font = new Font("Consolas", 8);
            using var brush = new SolidBrush(AxisColor);

            double xStart = Math.Ceiling(xMin / stepX) * stepX;
            for (double x = xStart; x <= xMax + 1e-9; x += stepX)
            {
                float px = (float)mapX(x);

                g.DrawLine(gridPen, px, area.Top, px, area.Bottom);

                string label = FormatNumber(x);
                var sz = g.MeasureString(label, font);
                float tx = px - sz.Width / 2f;
                float ty = area.Bottom - sz.Height - 2;

                if (tx < area.Left) tx = area.Left;
                if (tx + sz.Width > area.Right) tx = area.Right - sz.Width;

                g.DrawString(label, font, brush, tx, ty);
            }

            double yStart = Math.Ceiling(yMin / stepY) * stepY;
            for (double y = yStart; y <= yMax + 1e-9; y += stepY)
            {
                float py = (float)mapY(y);

                g.DrawLine(gridPen, area.Left, py, area.Right, py);

                string label = FormatNumber(y);
                var sz = g.MeasureString(label, font);
                float tx = area.Left + 4;
                float ty = py - sz.Height / 2f;

                if (ty < area.Top) ty = area.Top;
                if (ty + sz.Height > area.Bottom) ty = area.Bottom - sz.Height;

                g.DrawString(label, font, brush, tx, ty);
            }

            if (yMin <= 0 && 0 <= yMax)
            {
                float py0 = (float)mapY(0);
                g.DrawLine(axisPen, area.Left, py0, area.Right, py0);
            }
            if (xMin <= 0 && 0 <= xMax)
            {
                float px0 = (float)mapX(0);
                g.DrawLine(axisPen, px0, area.Top, px0, area.Bottom);
            }

            g.DrawRectangle(axisPen, area);
        }

        private static string FormatNumber(double v)
        {
            if (Math.Abs(v) < 1e-12) v = 0;
            return v.ToString("0.###");
        }

        private static double NiceStep(double raw)
        {
            if (raw <= 0) return 1;
            double exp = Math.Floor(Math.Log10(raw));
            double baseVal = raw / Math.Pow(10, exp);
            double nice = baseVal < 1.5 ? 1 : baseVal < 3 ? 2 : baseVal < 7 ? 5 : 10;
            return nice * Math.Pow(10, exp);
        }
    }
}