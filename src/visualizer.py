import math
from pathlib import Path
from typing import Dict, List, Any, Tuple
from PIL import Image, ImageDraw, ImageFont

def _get_font(size: int=14):
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', size)
    except Exception:
        try:
            font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', size)
        except Exception:
            font = ImageFont.load_default()
    return font

def plot_bar_chart(categories: List[str], series_data: Dict[str, List[float]], title: str, xlabel: str, ylabel: str, output_path: str, colors: Optional[Dict[str, Tuple[int, int, int]]]=None, width: int=1000, height: int=600):
    img = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    margin_left = 110
    margin_right = 160
    margin_top = 70
    margin_bottom = 90
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom
    default_palette = [(41, 128, 185), (231, 76, 60), (39, 174, 96), (243, 156, 18), (142, 68, 173), (52, 73, 94)]
    series_names = list(series_data.keys())
    if colors is None:
        colors = {name: default_palette[i % len(default_palette)] for i, name in enumerate(series_names)}
    max_val = 0.0
    for vals in series_data.values():
        max_val = max(max_val, max(vals) if vals else 0.0)
    max_val = max(10.0, max_val * 1.15)
    power = 10 ** math.floor(math.log10(max_val))
    max_val = math.ceil(max_val / power) * power
    num_ticks = 5
    for i in range(num_ticks + 1):
        y_val = max_val / num_ticks * i
        y_pos = margin_top + plot_h - int(y_val / max_val * plot_h)
        draw.line([(margin_left, y_pos), (margin_left + plot_w, y_pos)], fill=(230, 230, 230), width=1)
        draw.text((margin_left - 85, y_pos - 8), f'{int(y_val):,}', fill=(60, 60, 60), font=_get_font(12))
    draw.line([(margin_left, margin_top), (margin_left, margin_top + plot_h)], fill=(40, 40, 40), width=2)
    draw.line([(margin_left, margin_top + plot_h), (margin_left + plot_w, margin_top + plot_h)], fill=(40, 40, 40), width=2)
    n_groups = len(categories)
    n_series = len(series_names)
    group_width = plot_w / n_groups
    bar_width = group_width * 0.75 / n_series
    for g_idx, cat in enumerate(categories):
        group_center_x = margin_left + (g_idx + 0.5) * group_width
        start_x = group_center_x - n_series * bar_width / 2.0
        for s_idx, s_name in enumerate(series_names):
            val = series_data[s_name][g_idx]
            bar_h = int(val / max_val * plot_h)
            bx1 = start_x + s_idx * bar_width
            bx2 = bx1 + bar_width - 3
            by2 = margin_top + plot_h
            by1 = by2 - bar_h
            color = colors.get(s_name, (100, 100, 100))
            draw.rectangle([bx1, by1, bx2, by2], fill=color, outline=(30, 30, 30))
        draw.text((group_center_x - 35, margin_top + plot_h + 15), cat, fill=(30, 30, 30), font=_get_font(13))
    draw.text((margin_left + plot_w // 2 - len(title) * 4, 25), title, fill=(20, 20, 20), font=_get_font(18))
    draw.text((margin_left + plot_w // 2 - 40, height - 35), xlabel, fill=(40, 40, 40), font=_get_font(13))
    draw.text((15, margin_top - 30), ylabel, fill=(40, 40, 40), font=_get_font(13))
    leg_x = margin_left + plot_w + 20
    leg_y = margin_top + 20
    draw.text((leg_x, leg_y - 25), 'Schedulers', fill=(20, 20, 20), font=_get_font(14))
    for i, s_name in enumerate(series_names):
        curr_y = leg_y + i * 28
        c = colors.get(s_name, (100, 100, 100))
        draw.rectangle([leg_x, curr_y, leg_x + 18, curr_y + 18], fill=c, outline=(30, 30, 30))
        draw.text((leg_x + 26, curr_y + 2), s_name, fill=(40, 40, 40), font=_get_font(12))
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)

def plot_calibration_diagram(calibration_data: Dict[str, Any], output_path: str, width: int=800, height: int=600):
    img = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    margin_left = 90
    margin_right = 60
    margin_top = 70
    margin_bottom = 80
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom
    for i in range(6):
        val = i / 5.0
        x_pos = margin_left + int(val * plot_w)
        y_pos = margin_top + plot_h - int(val * plot_h)
        draw.line([(margin_left, y_pos), (margin_left + plot_w, y_pos)], fill=(235, 235, 235), width=1)
        draw.line([(x_pos, margin_top), (x_pos, margin_top + plot_h)], fill=(235, 235, 235), width=1)
        draw.text((margin_left - 40, y_pos - 8), f'{val:.1f}', fill=(60, 60, 60), font=_get_font(12))
        draw.text((x_pos - 10, margin_top + plot_h + 10), f'{val:.1f}', fill=(60, 60, 60), font=_get_font(12))
    draw.line([(margin_left, margin_top + plot_h), (margin_left + plot_w, margin_top)], fill=(180, 180, 180), width=2)
    bins = calibration_data.get('bins', [])
    n_bins = len(bins)
    bin_width = plot_w / max(1, n_bins)
    for i, b in enumerate(bins):
        acc = b['accuracy']
        conf = b['confidence']
        bx1 = margin_left + int(i * bin_width) + 8
        bx2 = margin_left + int((i + 1) * bin_width) - 8
        by2 = margin_top + plot_h
        by1 = by2 - int(acc * plot_h)
        draw.rectangle([bx1, by1, bx2, by2], fill=(52, 152, 219), outline=(41, 128, 185))
        conf_y = margin_top + plot_h - int(conf * plot_h)
        draw.line([(bx1, conf_y), (bx2, conf_y)], fill=(231, 76, 60), width=4)
    draw.line([(margin_left, margin_top), (margin_left, margin_top + plot_h)], fill=(30, 30, 30), width=2)
    draw.line([(margin_left, margin_top + plot_h), (margin_left + plot_w, margin_top + plot_h)], fill=(30, 30, 30), width=2)
    title = 'Confidence Calibration: Reliability Diagram'
    draw.text((margin_left + 100, 25), title, fill=(20, 20, 20), font=_get_font(18))
    draw.text((margin_left + plot_w // 2 - 60, height - 35), 'Predicted Confidence Bin', fill=(40, 40, 40), font=_get_font(13))
    draw.text((15, margin_top - 30), 'Empirical Accuracy', fill=(40, 40, 40), font=_get_font(13))
    ece = calibration_data.get('ece', 0.0)
    conf_margin = calibration_data.get('conf_margin', 0.0)
    info_text = f'Expected Calibration Error (ECE): {ece:.3f} | Correct vs Incorrect Confidence Gap: +{conf_margin:.3f}'
    draw.text((margin_left + 40, margin_top + 15), info_text, fill=(39, 174, 96), font=_get_font(13))
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)

def plot_trajectory_shift(requests: List[int], decisions: List[Any], output_path: str, width: int=1000, height: int=550):
    img = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    margin_left = 80
    margin_right = 50
    margin_top = 65
    margin_bottom = 75
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom
    n_reqs = len(requests)
    max_cyl = 200
    for cyl in [0, 50, 100, 150, 200]:
        y = margin_top + plot_h - int(cyl / max_cyl * plot_h)
        draw.line([(margin_left, y), (margin_left + plot_w, y)], fill=(240, 240, 240), width=1)
        draw.text((margin_left - 45, y - 7), f'{cyl}', fill=(70, 70, 70), font=_get_font(11))
    phase_colors = {0: (235, 245, 255), 1: (254, 249, 231), 2: (253, 237, 236), 3: (234, 250, 234)}
    phase_labels = ['Phase 1: Sequential', 'Phase 2: Uniform Random', 'Phase 3: Bursty Hotspots', 'Phase 4: Mixed Shifts']
    phase_size = n_reqs // 4
    for p in range(4):
        x1 = margin_left + int(p * phase_size / n_reqs * plot_w)
        x2 = margin_left + int((p + 1) * phase_size / n_reqs * plot_w)
        draw.rectangle([x1, margin_top, x2, margin_top + plot_h], fill=phase_colors[p])
        draw.line([(x2, margin_top), (x2, margin_top + plot_h)], fill=(180, 180, 180), width=1)
        draw.text((x1 + 15, margin_top + 10), phase_labels[p], fill=(50, 50, 50), font=_get_font(12))
    for idx, cyl in enumerate(requests):
        x = margin_left + int(idx / n_reqs * plot_w)
        y = margin_top + plot_h - int(cyl / max_cyl * plot_h)
        draw.ellipse([x - 1, y - 1, x + 1, y + 1], fill=(41, 128, 185))
    sched_colors = {'SSTF': (39, 174, 96), 'SCAN': (230, 126, 34), 'C-SCAN': (155, 89, 182), 'FCFS': (52, 73, 94)}
    for d in decisions:
        mid_idx = d.window_idx * len(d.requests) + len(d.requests) // 2
        x = margin_left + int(mid_idx / n_reqs * plot_w)
        y = margin_top + plot_h + 12
        c = sched_colors.get(d.predicted_scheduler, (100, 100, 100))
        draw.rectangle([x - 4, y, x + 4, y + 10], fill=c, outline=(20, 20, 20))
    draw.line([(margin_left, margin_top), (margin_left, margin_top + plot_h)], fill=(30, 30, 30), width=2)
    draw.line([(margin_left, margin_top + plot_h), (margin_left + plot_w, margin_top + plot_h)], fill=(30, 30, 30), width=2)
    title = 'Workload Shift Timeline: Request Access Pattern & Dynamic Selector Decisions'
    draw.text((margin_left + 40, 25), title, fill=(20, 20, 20), font=_get_font(16))
    draw.text((margin_left + plot_w // 2 - 50, height - 30), 'Request Arrival Sequence', fill=(40, 40, 40), font=_get_font(13))
    draw.text((15, margin_top - 25), 'Cylinder #', fill=(40, 40, 40), font=_get_font(13))
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)

def plot_feature_importances(feat_importances: Dict[str, float], output_path: str, width: int=800, height: int=500):
    img = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    margin_left = 200
    margin_right = 50
    margin_top = 60
    margin_bottom = 60
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom
    sorted_feats = sorted(feat_importances.items(), key=lambda x: x[1], reverse=True)
    n_feats = len(sorted_feats)
    bar_height = plot_h / n_feats * 0.7
    gap = plot_h / n_feats
    max_imp = max((val for _, val in sorted_feats)) if sorted_feats else 1.0
    max_imp = max(0.2, max_imp * 1.15)
    for i in range(5):
        val = max_imp / 4 * i
        x = margin_left + int(val / max_imp * plot_w)
        draw.line([(x, margin_top), (x, margin_top + plot_h)], fill=(235, 235, 235), width=1)
        draw.text((x - 12, margin_top + plot_h + 10), f'{val:.2f}', fill=(60, 60, 60), font=_get_font(11))
    for i, (name, val) in enumerate(sorted_feats):
        y1 = margin_top + int(i * gap + (gap - bar_height) / 2)
        y2 = y1 + int(bar_height)
        bx = margin_left + int(val / max_imp * plot_w)
        draw.rectangle([margin_left, y1, bx, y2], fill=(46, 204, 113), outline=(39, 174, 96))
        clean_name = name.replace('_', ' ').title()
        draw.text((margin_left - 185, y1 + 3), clean_name, fill=(30, 30, 30), font=_get_font(12))
        draw.text((bx + 8, y1 + 3), f'{val * 100:.1f}%', fill=(50, 50, 50), font=_get_font(11))
    draw.line([(margin_left, margin_top), (margin_left, margin_top + plot_h)], fill=(30, 30, 30), width=2)
    draw.line([(margin_left, margin_top + plot_h), (margin_left + plot_w, margin_top + plot_h)], fill=(30, 30, 30), width=2)
    draw.text((margin_left + 30, 20), 'Learned Selector: Window Feature Importance (Gini)', fill=(20, 20, 20), font=_get_font(16))
    draw.text((margin_left + plot_w // 2 - 40, height - 25), 'Relative Importance', fill=(40, 40, 40), font=_get_font(12))
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
