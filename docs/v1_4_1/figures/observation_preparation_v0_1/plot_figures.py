"""Render existing Engineering values only; no producer/analyzer/CUDA imports.

Run from repository root: python docs/v1_4_1/figures/observation_preparation_v0_1/plot_figures.py
The small coordinator CSV must already exist. All A values come from report §9.4.
"""
import csv
import hashlib
import json
from decimal import Decimal
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Patch
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
REPORT = ROOT / 'docs/v1_4_1/coe_research_short_note_v0_1.md'
CSV = ROOT / '.local/diagnostics/observation_engineering_review_8c8e993d38cf4c7c93b151e986e2a4e8/operations.csv'
CSV_SHA = '5a56d6857bd1d567fe826e73090f1330ed57334c64acc6fe28d8e52f0d094705'
NAMES = ['Host path', 'CUDA API', 'Device wait', 'Sync residual', 'Unattributed']
COLORS = ['#0077BB', '#BBBBBB', '#EE7733', '#AA3377', '#000000']
HATCHES = ['', '//', 'xx', '..', '++']
ORDER = [(b, n, v) for b in (1, 2) for n in (32, 512) for v in ('O', 'P')]
LABELS = [f'b{b} / {n}{v}' for b, n, v in ORDER]
plt.rcParams.update({'font.family': 'sans-serif', 'font.sans-serif': ['Microsoft YaHei', 'DejaVu Sans'],
    'font.size': 10, 'axes.titlesize': 12, 'axes.labelsize': 10,
    'xtick.labelsize': 9, 'ytick.labelsize': 9, 'legend.fontsize': 10,
    'savefig.dpi': 300, 'axes.spines.top': False, 'axes.spines.right': False,
    'svg.hashsalt': 'observation-preparation-v0.1'})


def digest(value):
    return hashlib.sha256(value).hexdigest()


def load_values():
    raw = CSV.read_bytes()
    if digest(raw) != CSV_SHA:
        raise ValueError('operations.csv identity changed')
    operations = list(csv.DictReader(raw.decode('utf-8-sig').splitlines()))
    budgets = []
    for line in REPORT.read_text(encoding='utf-8').splitlines():
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if len(cells) != 11 or cells[0] not in ('1', '2') or cells[2] not in ('Request', 'Prefill', 'Decode'):
            continue
        ns = [int(Decimal(x) * 1_000_000) for x in cells[3:]]
        total, host, api, submit, non_submit, wait, residual, unknown = ns
        if total != host + api + wait + residual + unknown or api != submit + non_submit:
            raise ValueError('Report A arithmetic changed')
        budgets.append(dict(block=int(cells[0]), condition=cells[1], phase=cells[2], total_ns=total,
            categories_ns=[host, api, wait, residual, unknown],
            categories_percent=[100 * x / total for x in [host, api, wait, residual, unknown]],
            api_submit_ns=submit, api_non_submit_ns=non_submit))
    a = {(r['block'], r['condition'], r['phase']): r for r in budgets}
    o = {(int(r['block']), int(r['input_tokens']), r['variant'], int(r['token'])): r for r in operations}
    if len(a) != 24 or len(o) != 16 or len(budgets) != 24 or len(operations) != 16:
        raise ValueError('Missing or duplicate original row')
    for (b, n, v, t), r in o.items():
        q = a[b, f'{n}{v}', ('Prefill', 'Decode')[t]]
        if q['total_ns'] != int(r['phase_total_ns']) or q['categories_ns'][:4] != [
                int(r[k]) for k in ['a_host_ns', 'a_api_ns', 'a_sync_wait_ns', 'a_residual_ns']]:
            raise ValueError('CSV/report phase A mismatch')
        r['coe_percent_of_phase'] = 100 * int(r['coe_ns']) / q['total_ns']
    for b, n, v in ORDER:
        r, p, d = [a[b, f'{n}{v}', phase] for phase in ('Request', 'Prefill', 'Decode')]
        if r['total_ns'] != p['total_ns'] + d['total_ns'] or r['categories_ns'] != [
                x + y for x, y in zip(p['categories_ns'], d['categories_ns'])]:
            raise ValueError('Request/phase mismatch')
    return budgets, operations, a, o


def save(fig, name):
    fig.savefig(HERE / f'{name}.png', bbox_inches='tight', facecolor='white')
    svg = HERE / f'{name}.svg'
    fig.savefig(svg, bbox_inches='tight', facecolor='white', metadata={'Date': None})
    # Windows plotting backends emit CRLF/path trailing spaces; format only.
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text(encoding='utf-8').splitlines())+'\n',
        encoding='utf-8', newline='\n')
    plt.close(fig)


def draw_a(a):
    fig, axes = plt.subplots(3, 2, figsize=(12.2, 11.5))
    for row, phase in enumerate(('Request', 'Prefill', 'Decode')):
        selected = [a[b, f'{n}{v}', phase] for b, n, v in ORDER]
        y = np.arange(8)
        for col, percent in enumerate((False, True)):
            ax = axes[row, col]
            values = np.array([r['categories_percent'] if percent else
                [x / 1e6 for x in r['categories_ns']] for r in selected])
            left = np.zeros(8)
            for k, (color, hatch) in enumerate(zip(COLORS, HATCHES)):
                ax.barh(y, values[:, k], left=left, height=.68, color=color, hatch=hatch,
                    edgecolor='#333333', linewidth=.25, label=NAMES[k])
                left += values[:, k]
            ax.set_yticks(y, LABELS)
            ax.invert_yaxis()
            ax.axhline(3.5, color='#444444', linestyle=':', linewidth=1)
            ax.set_title(f'{phase} | ' + ('逐窗口占比' if percent else '原A绝对预算'))
            ax.set_xlabel('原A / 本窗口总长 (%)' if percent else 'Wall-clock budget (ms)')
            ax.set_xlim(0, 100 if percent else max(r['total_ns'] for r in selected) / 1e6 * 1.14)
            if not percent:
                for j, r in enumerate(selected):
                    ax.text(r['total_ns'] / 1e6 + .8, j, f"{r['total_ns']/1e6:.2f}", va='center', fontsize=9)
            ax.grid(axis='x', alpha=.15)
            ax.set_axisbelow(True)
    fig.suptitle('原A五类：8次进程执行，24个窗口全部保留', y=.995, fontsize=15)
    handles = [Patch(facecolor=c, hatch=h, edgecolor='#333333', label=n)
        for n, c, h in zip(NAMES, COLORS, HATCHES)]
    fig.legend(handles=handles, loc='upper center', bbox_to_anchor=(.5, .965), ncol=5, frameon=False)
    fig.text(.5, .015, 'Engineering / P1 only；横虚线分隔block。每条独立显示，无均值/误差条。\n'
        'Device wait与residual很小；unattributed全部原值0，未抬高细条。COE不在此堆叠中。',
        ha='center', fontsize=10)
    fig.tight_layout(rect=(0, .06, 1, .925), h_pad=2)
    save(fig, 'original_a_absolute_and_percent')


def draw_coe(o):
    fig, axes = plt.subplots(2, 2, figsize=(12.2, 7.4))
    for token in (0, 1):
        selected = [o[b, n, v, token] for b, n, v in ORDER]
        for col, percent in enumerate((False, True)):
            ax = axes[token, col]
            values = [r['coe_percent_of_phase'] if percent else int(r['coe_ns']) / 1e6 for r in selected]
            bars = ax.bar(np.arange(8), values, color=['#0077BB' if v == 'O' else '#EE7733' for _, _, v in ORDER],
                edgecolor='#333333', linewidth=.6)
            for bar, (_, _, v) in zip(bars, ORDER):
                if v == 'P': bar.set_hatch('//')
            for j, value in enumerate(values):
                ax.text(j, value + max(values) * .025, f'{value:.3f}', ha='center', fontsize=9)
            ax.set_xticks(np.arange(8), LABELS, rotation=35, ha='right')
            ax.axvline(3.5, color='#444444', linestyle=':', linewidth=1)
            ax.set_ylim(0, max(values) * 1.2)
            ax.set_title(f'token {token} / ' + ('Prefill' if token == 0 else 'Decode'))
            ax.set_ylabel('COE / 对应phase (%)' if percent else 'COE (ms)')
            ax.set_xlabel('完整block中的输入长度与包装')
            ax.grid(axis='y', alpha=.15)
            ax.set_axisbelow(True)
    fig.suptitle('COE独立展示：必要活动交集，不加到原Device wait', y=.995, fontsize=15)
    fig.text(.5, .015, '全部16链；蓝色O，橙色斜纹P；无合并/删样本/显著性判断。\n'
        '占比分母为本条token对应phase总长，不是操作墙钟；不是纯Host阻塞率。', ha='center', fontsize=10)
    fig.tight_layout(rect=(0, .065, 1, .95))
    save(fig, 'coe_absolute_and_phase_percent')


def draw_flow():
    fig, ax = plt.subplots(figsize=(12.2, 6.9))
    ax.set_xlim(0, 12); ax.set_ylim(0, 7.0); ax.axis('off')
    def box(x, y, w, h, text, color):
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.08',facecolor=color,edgecolor='#444444',linewidth=.8))
        ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=10)
    def arrow(x1,y1,x2,y2):
        ax.annotate('', xy=(x2,y2),xytext=(x1,y1),arrowprops={'arrowstyle':'->','color':'#333333','lw':1.1})
    ax.text(0,6.75,'三层必须分开：计算、完成政策、测量包装',fontsize=16,fontweight='bold')
    box(.12,5.4,11.65,.8,'窗外：模型/输入上GPU → warmup3 → P预备不变标签（O无此步骤） → 成功final drain', '#F0F0F0')
    ax.text(.08,5.02,'① 模型计算（固定参考算法：eager/SDPA、KV cache、greedy argmax）',fontsize=11,fontweight='bold')
    box(.12,4.0,3.2,.72,'Prefill forward → argmax\n得到GPU上的首token ID', '#DCECF5')
    box(4.35,4.0,3.2,.72,'首token经②③完成后\nDecode forward / KV → argmax', '#DCECF5')
    arrow(3.4,4.36,4.25,4.36)
    box(8.55,4.0,3.2,.72,'输出数量/EOS政策\n本批固定输出2', '#DCECF5')
    arrow(7.65,4.36,8.45,4.36)
    ax.text(.08,3.62,'② 逐token完成政策（我们选定的执行方式，不是所有PyTorch程序的唯一流程）',fontsize=11,fontweight='bold')
    box(.12,2.55,3.15,.76,'GPU token → .cpu()\n复制helper内部copy → sync', '#DDF1E9')
    box(4.35,2.55,3.2,.76,'Host reshape/tolist/整数ID\n实际Host-readable后取时间T[i]', '#DDF1E9')
    box(8.55,2.55,3.2,.76,'Host token已取得\n不是文本/网络流式发送', '#DDF1E9')
    arrow(3.37,2.93,4.25,2.93); arrow(7.65,2.93,8.45,2.93)
    ax.text(.08,2.15,'③ 观测包装（有时延的研究代码；NVTX不是GPU完成证明）',fontsize=11,fontweight='bold')
    box(.12,.85,3.2,.94,'copy前：O现场校验/编码\nP现场cache绑定/消费检查\n两者P1均push实际NVTX范围', '#FFF0DE')
    box(4.35,.85,3.2,.94,'T[i]后：recorder校验/编码\n时钟夹界与point（P1）\n随后pop范围并继续', '#FFF0DE')
    box(8.55,.85,3.2,.94,'P0关闭Nsight/NVTX发射\n仍保留身份、recorder、clock\nP不是无插桩，也不是Cpre', '#FFF0DE')
    ax.text(.12,.23,'窗口：Request=[Tstart,Tlast)；Prefill=[Tstart,T0)；Decode=[T0,Tlast)。示意不按时长比例绘制。',fontsize=10)
    save(fig, 'execution_layers')


def main():
    budgets, operations, a, o = load_values()
    draw_flow(); draw_a(a); draw_coe(o)
    payload = dict(version='observation-presentation/0.1', role='Engineering',
        execution_analysis_commit='2d0d88e7553b11587d66132ec51f5956092a87e6',
        source_operations_sha256=CSV_SHA, source_a='coe_research_short_note_v0_1.md §9.4; first committed 22f2b04',
        a_category_order=NAMES, display_order=LABELS, a_rows=budgets, operation_rows=operations,
        percentage_rule='100*category_ns/this_window_total_ns; COE/associated_phase_total_ns',
        full_blocks=2, runs=8, token_chains=16,
        a_payload_sha256=digest(json.dumps(budgets,sort_keys=True,separators=(',',':')).encode()),
        plot_code_sha256=digest(Path(__file__).read_bytes()),
        limitations=['No A/COE migration','No uninstrumented equivalence','No inferential statistics'])
    (HERE/'chart_values.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(a_windows=len(budgets),coe_rows=len(operations),figures=3,
        source_csv_sha256=CSV_SHA,cohort='8 Engineering P1 / 2 blocks',producer_imported=False)))


if __name__ == '__main__':
    main()
