using System;
using System.Collections.Generic;
using System.Drawing;
using System.Windows.Forms;

namespace Lab1Graph
{
    public class MainForm : Form
    {
        private readonly GraphRenderer _renderer = new GraphRenderer();
        private readonly ComboBox _funcCombo = new ComboBox();
        private readonly Panel _canvas = new Panel();
        private readonly NumericUpDown _xMinBox = new NumericUpDown();
        private readonly NumericUpDown _xMaxBox = new NumericUpDown();
        private readonly Button _drawBtn = new Button();
        private readonly Label _status = new Label();

        private readonly Dictionary<string, Func<double, double>> _functions =
            new Dictionary<string, Func<double, double>>
        {
            { "sin(x)",          x => Math.Sin(x) },
            { "cos(x)",          x => Math.Cos(x) },
            { "x^2",             x => x * x },
            { "x^3",             x => x * x * x },
            { "x^3 - 3x",        x => x * x * x - 3 * x },
            { "1 / x",           x => x == 0 ? double.NaN : 1.0 / x },
            { "sqrt(x)",         x => x < 0 ? double.NaN : Math.Sqrt(x) },
            { "exp(x)",          x => Math.Exp(x) },
            { "ln(x)",           x => x <= 0 ? double.NaN : Math.Log(x) },
            { "sin(x)/x",        x => x == 0 ? 1.0 : Math.Sin(x) / x },
        };

        public MainForm()
        {
            Text = "Лабораторная работа №1";
            Width = 1000;
            Height = 700;
            StartPosition = FormStartPosition.CenterScreen;
            MinimumSize = new Size(500, 400);

            BuildUi();

            _canvas.Paint += Canvas_Paint;
            _canvas.Resize += (s, e) => _canvas.Invalidate();

            SelectDefaultSin();
        }

        private void SelectDefaultSin()
        {
            _funcCombo.SelectedIndex = 0; 
            _xMinBox.Value = -10m;
            _xMaxBox.Value = 10m;
            _canvas.Invalidate();
        }

        private void BuildUi()
        {
            var top = new Panel { Dock = DockStyle.Top, Height = 44, Padding = new Padding(6) };

            var lblFunc = new Label { Text = "Функция:", Left = 6, Top = 13, Width = 60 };
            _funcCombo.Left = 68; _funcCombo.Top = 9; _funcCombo.Width = 140;
            _funcCombo.DropDownStyle = ComboBoxStyle.DropDownList;
            _funcCombo.Items.AddRange(new object[]
            {
                "sin(x)", "cos(x)", "x^2", "x^3", "x^3 - 3x",
                "1 / x", "sqrt(x)", "exp(x)", "ln(x)", "sin(x)/x"
            });
            _funcCombo.SelectedIndexChanged += (s, e) => _canvas.Invalidate();

            var lblXMin = new Label { Text = "x от:", Left = 220, Top = 13, Width = 40 };
            _xMinBox.Left = 262; _xMinBox.Top = 9; _xMinBox.Width = 70;
            _xMinBox.DecimalPlaces = 2; _xMinBox.Minimum = -1000; _xMinBox.Maximum = 1000;
            _xMinBox.Increment = 1;

            var lblXMax = new Label { Text = "до:", Left = 340, Top = 13, Width = 30 };
            _xMaxBox.Left = 372; _xMaxBox.Top = 9; _xMaxBox.Width = 70;
            _xMaxBox.DecimalPlaces = 2; _xMaxBox.Minimum = -1000; _xMaxBox.Maximum = 1000;
            _xMaxBox.Increment = 1;

            _drawBtn.Text = "Построить"; _drawBtn.Left = 456; _drawBtn.Top = 8;
            _drawBtn.Width = 90; _drawBtn.Height = 26;
            _drawBtn.Click += (s, e) =>
            {
                if (_xMaxBox.Value <= _xMinBox.Value)
                {
                    MessageBox.Show("Правая граница должна быть больше левой.");
                    return;
                }
                _canvas.Invalidate();
            };

            _status.Text = "Измените размер окна: график масштабируется автоматически";
            _status.Left = 560; _status.Top = 13; _status.Width = 400;
            _status.ForeColor = Color.DimGray;

            top.Controls.AddRange(new Control[]
            {
                lblFunc, _funcCombo, lblXMin, _xMinBox, lblXMax, _xMaxBox,
                _drawBtn, _status
            });

            _canvas.Dock = DockStyle.Fill;
            _canvas.BackColor = Color.White;
            _canvas.DoubleBuffered(true); 

            Controls.Add(_canvas);
            Controls.Add(top);
        }

        private void Canvas_Paint(object? sender, PaintEventArgs e)
        {
            if (_funcCombo.SelectedItem is not string name) return;
            if (!_functions.TryGetValue(name, out var f)) return;

            double xMin = (double)_xMinBox.Value;
            double xMax = (double)_xMaxBox.Value;
            if (xMax <= xMin) return;

            var area = new Rectangle(
                _canvas.ClientRectangle.Left + 40,
                _canvas.ClientRectangle.Top + 10,
                _canvas.ClientRectangle.Width - 60,
                _canvas.ClientRectangle.Height - 40);

            if (area.Width <= 10 || area.Height <= 10) return;

            _renderer.Draw(e.Graphics, area, f, xMin, xMax);

            using var fnt = new Font("Segoe UI", 10, FontStyle.Bold);
            e.Graphics.DrawString($"y = {name}", fnt, Brushes.DarkBlue,
                area.Left + 6, area.Top + 4);
        }
    }

    internal static class ControlExtensions
    {
        public static void DoubleBuffered(this Control control, bool value)
        {
            var prop = typeof(Control).GetProperty("DoubleBuffered",
                System.Reflection.BindingFlags.Instance |
                System.Reflection.BindingFlags.NonPublic);
            prop?.SetValue(control, value, null);
        }
    }
}