import math
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont

def _get_font(size: int = 14, bold: bool = True):
    font_files = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
    ]
    for fp in font_files:
        try:
            return ImageFont.truetype(fp, size)
        except Exception:
            continue
    return ImageFont.load_default()

def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> Tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

def plot_bar_chart(categories: List[str], series_data: Dict[str, List[float]], title: str, xlabel: str, ylabel: str, output_path: str, colors: Optional[Dict[str, Tuple[int, int, int]]] = None, width: int = 980, height: int = 560):
    img = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    margin_left = 115
    margin_right = 215
    margin_top = 75
    margin_bottom = 95
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom

    default_palette = [
        (41, 128, 185),   # FCFS: Blue
        (39, 174, 96),    # SSTF: Green
        (230, 126, 34),   # SCAN: Orange
        (155, 89, 182),   # C-SCAN: Purple
        (231, 76, 60),    # Learned: Red
        (52, 73, 94)      # Oracle: Navy
    ]
    series_names = list(series_data.keys())
    if colors is None:
        colors = {name: default_palette[i % len(default_palette)] for i, name in enumerate(series_names)}

    max_val = 0.0
    for vals in series_data.values():
        max_val = max(max_val, max(vals) if vals else 0.0)
    max_val = max(10.0, max_val * 1.12)
    power = 10 ** math.floor(math.log10(max_val))
    max_val = math.ceil(max_val / power) * power

    num_ticks = 5
    font_tick = _get_font(18, bold=True)
    for i in range(num_ticks + 1):
        y_val = max_val / num_ticks * i
        y_pos = margin_top + plot_h - int((y_val / max_val) * plot_h)
        draw.line([(margin_left, y_pos), (margin_left + plot_w, y_pos)], fill=(225, 225, 225), width=1)
        val_str = f"{int(y_val):,}"
        tw, th = _text_size(draw, val_str, font_tick)
        draw.text((margin_left - tw - 12, y_pos - th // 2), val_str, fill=(50, 50, 50), font=font_tick)

    draw.line([(margin_left, margin_top), (margin_left, margin_top + plot_h)], fill=(30, 30, 30), width=3)
    draw.line([(margin_left, margin_top + plot_h), (margin_left + plot_w, margin_top + plot_h)], fill=(30, 30, 30), width=3)

    n_groups = len(categories)
    n_series = len(series_names)
    group_width = plot_w / n_groups
    bar_width = group_width * 0.80 / n_series

    font_cat = _get_font(18, bold=True)
    for g_idx, cat in enumerate(categories):
        group_center_x = margin_left + (g_idx + 0.5) * group_width
        start_x = group_center_x - (n_series * bar_width) / 2.0
        for s_idx, s_name in enumerate(series_names):
            val = series_data[s_name][g_idx]
            bar_h = int((val / max_val) * plot_h)
            bx1 = start_x + s_idx * bar_width
            bx2 = bx1 + bar_width - 3
            by2 = margin_top + plot_h
            by1 = by2 - bar_h
            color = colors.get(s_name, (100, 100, 100))
            draw.rectangle([bx1, by1, bx2, by2], fill=color, outline=(20, 20, 20), width=1)
        
        tw, th = _text_size(draw, cat, font_cat)
        draw.text((group_center_x - tw // 2, margin_top + plot_h + 14), cat, fill=(20, 20, 20), font=font_cat)

    font_title = _get_font(23, bold=True)
    tw, _ = _text_size(draw, title, font_title)
    draw.text((margin_left + (plot_w - tw) // 2, 16), title, fill=(10, 10, 10), font=font_title)

    font_lbl = _get_font(20, bold=True)
    tw, _ = _text_size(draw, xlabel, font_lbl)
    draw.text((margin_left + (plot_w - tw) // 2, height - 38), xlabel, fill=(30, 30, 30), font=font_lbl)
    draw.text((margin_left - 20, margin_top - 34), ylabel, fill=(30, 30, 30), font=font_lbl)

    leg_x = margin_left + plot_w + 14
    leg_y = margin_top + 10
    draw.rectangle([leg_x - 6, leg_y - 6, width - 12, leg_y + n_series * 34 + 36], fill=(248, 249, 250), outline=(190, 190, 190), width=1)
    
    font_leg_hdr = _get_font(18, bold=True)
    draw.text((leg_x, leg_y), "Schedulers", fill=(10, 10, 10), font=font_leg_hdr)
    
    font_leg = _get_font(16, bold=True)
    for i, s_name in enumerate(series_names):
        curr_y = leg_y + 30 + i * 32
        c = colors.get(s_name, (100, 100, 100))
        draw.rectangle([leg_x, curr_y, leg_x + 20, curr_y + 20], fill=c, outline=(20, 20, 20), width=1)
        draw.text((leg_x + 26, curr_y + 1), s_name, fill=(30, 30, 30), font=font_leg)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)

def plot_calibration_diagram(calibration_data: Dict[str, Any], output_path: str, width: int = 820, height: int = 570):
    img = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    margin_left = 110
    margin_right = 50
    margin_top = 105
    margin_bottom = 90
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom

    font_tick = _get_font(18, bold=True)
    for i in range(6):
        val = i / 5.0
        x_pos = margin_left + int(val * plot_w)
        y_pos = margin_top + plot_h - int(val * plot_h)
        draw.line([(margin_left, y_pos), (margin_left + plot_w, y_pos)], fill=(230, 230, 230), width=1)
        draw.line([(x_pos, margin_top), (x_pos, margin_top + plot_h)], fill=(230, 230, 230), width=1)
        
        tw, th = _text_size(draw, f"{val:.1f}", font_tick)
        draw.text((margin_left - tw - 12, y_pos - th // 2), f"{val:.1f}", fill=(50, 50, 50), font=font_tick)
        draw.text((x_pos - tw // 2, margin_top + plot_h + 12), f"{val:.1f}", fill=(50, 50, 50), font=font_tick)

    # Ideal calibration line
    draw.line([(margin_left, margin_top + plot_h), (margin_left + plot_w, margin_top)], fill=(160, 160, 160), width=3)

    bins = calibration_data.get('bins', [])
    n_bins = len(bins)
    bin_width = plot_w / max(1, n_bins)

    for i, b in enumerate(bins):
        acc = b['accuracy']
        conf = b['confidence']
        bx1 = margin_left + int(i * bin_width) + 12
        bx2 = margin_left + int((i + 1) * bin_width) - 12
        by2 = margin_top + plot_h
        by1 = by2 - int(acc * plot_h)
        draw.rectangle([bx1, by1, bx2, by2], fill=(52, 152, 219), outline=(41, 128, 185), width=2)
        conf_y = margin_top + plot_h - int(conf * plot_h)
        draw.line([(bx1, conf_y), (bx2, conf_y)], fill=(231, 76, 60), width=6)

    draw.line([(margin_left, margin_top), (margin_left, margin_top + plot_h)], fill=(20, 20, 20), width=3)
    draw.line([(margin_left, margin_top + plot_h), (margin_left + plot_w, margin_top + plot_h)], fill=(20, 20, 20), width=3)

    font_title = _get_font(23, bold=True)
    title = "Confidence Calibration: Reliability Diagram"
    tw, _ = _text_size(draw, title, font_title)
    draw.text((margin_left + (plot_w - tw) // 2, 14), title, fill=(10, 10, 10), font=font_title)

    font_lbl = _get_font(20, bold=True)
    tw, _ = _text_size(draw, "Predicted Confidence Bin", font_lbl)
    draw.text((margin_left + (plot_w - tw) // 2, height - 36), "Predicted Confidence Bin", fill=(30, 30, 30), font=font_lbl)
    draw.text((margin_left - 20, margin_top - 32), "Empirical Accuracy", fill=(30, 30, 30), font=font_lbl)

    ece = calibration_data.get('ece', 0.0)
    conf_margin = calibration_data.get('conf_margin', 0.0)
    info_text = f"Expected Calibration Error (ECE): {ece:.4f}  |  Calibration Margin: +{conf_margin:.4f}"
    font_badge = _get_font(17, bold=True)
    tw, th = _text_size(draw, info_text, font_badge)
    badge_x = margin_left + (plot_w - tw) // 2
    badge_y = 52
    draw.rectangle([badge_x - 10, badge_y - 5, badge_x + tw + 10, badge_y + th + 5], fill=(234, 250, 234), outline=(39, 174, 96), width=1)
    draw.text((badge_x, badge_y), info_text, fill=(24, 134, 75), font=font_badge)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)

def plot_trajectory_shift(requests: List[int], decisions: List[Any], output_path: str, width: int = 1200, height: int = 580):
    img = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    margin_left = 135
    margin_right = 50
    margin_top = 95
    margin_bottom = 95
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom

    n_reqs = len(requests)
    max_cyl = 200

    phase_colors = [
        (235, 245, 255),  # Phase 1: Blue tint
        (255, 250, 230),  # Phase 2: Yellow tint
        (253, 237, 236),  # Phase 3: Red tint
        (234, 250, 234),  # Phase 4: Green tint
    ]
    phase_labels = [
        'Phase 1: Sequential',
        'Phase 2: Uniform Random',
        'Phase 3: Bursty Hotspots',
        'Phase 4: Mixed Shifts'
    ]
    phase_size = n_reqs // 4
    font_phase = _get_font(18, bold=True)
    
    # Phase ribbons above plot area
    ribbon_y1 = margin_top - 36
    ribbon_y2 = margin_top - 4
    for p in range(4):
        x1 = margin_left + int(p * phase_size / n_reqs * plot_w)
        x2 = margin_left + int((p + 1) * phase_size / n_reqs * plot_w)
        # Background of plot area
        draw.rectangle([x1, margin_top, x2, margin_top + plot_h], fill=phase_colors[p])
        draw.line([(x2, margin_top), (x2, margin_top + plot_h)], fill=(160, 160, 160), width=2)
        # Dedicated top ribbon
        draw.rectangle([x1, ribbon_y1, x2, ribbon_y2], fill=phase_colors[p], outline=(150, 150, 150), width=1)
        tw, th = _text_size(draw, phase_labels[p], font_phase)
        draw.text((x1 + ((x2 - x1) - tw) // 2, ribbon_y1 + (ribbon_y2 - ribbon_y1 - th) // 2), phase_labels[p], fill=(30, 30, 30), font=font_phase)

    font_tick = _get_font(18, bold=True)
    for cyl in [0, 50, 100, 150, 200]:
        y = margin_top + plot_h - int(cyl / max_cyl * plot_h)
        draw.line([(margin_left, y), (margin_left + plot_w, y)], fill=(235, 235, 235), width=1)
        tw, th = _text_size(draw, f"{cyl}", font_tick)
        draw.text((margin_left - tw - 12, y - th // 2), f"{cyl}", fill=(50, 50, 50), font=font_tick)

    # Plot cylinder requests
    for idx, cyl in enumerate(requests):
        x = margin_left + int(idx / n_reqs * plot_w)
        y = margin_top + plot_h - int(cyl / max_cyl * plot_h)
        draw.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(31, 110, 165))

    # Plot scheduler selection markers
    sched_colors = {
        'SSTF': (39, 174, 96),     # Green
        'SCAN': (230, 126, 34),    # Orange
        'C-SCAN': (155, 89, 182),  # Purple
        'FCFS': (52, 73, 94)       # Navy
    }
    for d in decisions:
        mid_idx = d.window_idx * len(d.requests) + len(d.requests) // 2
        x = margin_left + int(mid_idx / n_reqs * plot_w)
        y = margin_top + plot_h + 10
        c = sched_colors.get(d.predicted_scheduler, (100, 100, 100))
        draw.rectangle([x - 6, y, x + 6, y + 16], fill=c, outline=(20, 20, 20), width=1)

    draw.line([(margin_left, margin_top), (margin_left, margin_top + plot_h)], fill=(20, 20, 20), width=3)
    draw.line([(margin_left, margin_top + plot_h), (margin_left + plot_w, margin_top + plot_h)], fill=(20, 20, 20), width=3)

    font_title = _get_font(24, bold=True)
    title = 'Workload Shift Timeline: Request Access Pattern & Dynamic Selector Decisions'
    tw, _ = _text_size(draw, title, font_title)
    draw.text((margin_left + (plot_w - tw) // 2, 16), title, fill=(10, 10, 10), font=font_title)

    font_lbl = _get_font(20, bold=True)
    tw, _ = _text_size(draw, 'Request Arrival Sequence (1,000 Requests)', font_lbl)
    draw.text((margin_left + (plot_w - tw) // 2, height - 34), 'Request Arrival Sequence (1,000 Requests)', fill=(30, 30, 30), font=font_lbl)
    draw.text((margin_left - 110, margin_top - 36), 'Cylinder #', fill=(30, 30, 30), font=font_lbl)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)

def plot_feature_importances(feat_importances: Dict[str, float], output_path: str, width: int = 880, height: int = 560):
    img = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    margin_left = 275
    margin_right = 75
    margin_top = 70
    margin_bottom = 70
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom

    sorted_feats = sorted(feat_importances.items(), key=lambda x: x[1], reverse=True)
    n_feats = len(sorted_feats)
    bar_height = plot_h / n_feats * 0.72
    gap = plot_h / n_feats

    max_imp = max((val for _, val in sorted_feats)) if sorted_feats else 1.0
    max_imp = max(0.2, max_imp * 1.15)

    font_tick = _get_font(18, bold=True)
    for i in range(5):
        val = max_imp / 4 * i
        x = margin_left + int(val / max_imp * plot_w)
        draw.line([(x, margin_top), (x, margin_top + plot_h)], fill=(230, 230, 230), width=1)
        val_str = f"{val:.2f}"
        tw, th = _text_size(draw, val_str, font_tick)
        draw.text((x - tw // 2, margin_top + plot_h + 12), val_str, fill=(50, 50, 50), font=font_tick)

    font_feat = _get_font(19, bold=True)
    font_pct = _get_font(17, bold=True)
    for i, (name, val) in enumerate(sorted_feats):
        y1 = margin_top + int(i * gap + (gap - bar_height) / 2)
        y2 = y1 + int(bar_height)
        bx = margin_left + int(val / max_imp * plot_w)
        draw.rectangle([margin_left, y1, bx, y2], fill=(46, 204, 113), outline=(39, 174, 96), width=1)
        
        clean_name = name.replace('_', ' ').title()
        tw, th = _text_size(draw, clean_name, font_feat)
        draw.text((margin_left - tw - 12, y1 + (int(bar_height) - th) // 2), clean_name, fill=(20, 20, 20), font=font_feat)
        
        pct_str = f"{val * 100:.1f}%"
        _, th_pct = _text_size(draw, pct_str, font_pct)
        draw.text((bx + 8, y1 + (int(bar_height) - th_pct) // 2), pct_str, fill=(30, 30, 30), font=font_pct)

    draw.line([(margin_left, margin_top), (margin_left, margin_top + plot_h)], fill=(20, 20, 20), width=3)
    draw.line([(margin_left, margin_top + plot_h), (margin_left + plot_w, margin_top + plot_h)], fill=(20, 20, 20), width=3)

    font_title = _get_font(23, bold=True)
    title = 'Learned Selector: Window Feature Importance (Gini)'
    tw, _ = _text_size(draw, title, font_title)
    draw.text((margin_left + (plot_w - tw) // 2, 18), title, fill=(10, 10, 10), font=font_title)

    font_lbl = _get_font(20, bold=True)
    tw, _ = _text_size(draw, 'Relative Importance Score', font_lbl)
    draw.text((margin_left + (plot_w - tw) // 2, height - 32), 'Relative Importance Score', fill=(30, 30, 30), font=font_lbl)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)



