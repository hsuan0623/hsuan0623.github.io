import numpy as np
from flask import Flask, render_template_string, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = 'ahp_super_secret_key'  # 供 Session 儲存暫存資料使用

# ==========================================
# AHP 核心計算邏輯
# ==========================================
def parse_value(val_str):
    """將下拉選單字串轉換為浮點數"""
    if '/' in val_str:
        num, den = val_str.split('/')
        return float(num) / float(den)
    return float(val_str)

def calculate_weights_by_idx(items_len, comparisons_dict):
    """依照索引建立成對比較矩陣，並計算權重"""
    n = items_len
    if n <= 1:
        return np.ones((1, 1)), np.array([1.0])
    matrix = np.ones((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            val = parse_value(comparisons_dict.get(f"{i}_{j}", "1"))
            matrix[i, j] = val
            matrix[j, i] = 1.0 / val
    row_products = np.prod(matrix, axis=1)
    geom_means = row_products ** (1.0 / n)
    weights = geom_means / np.sum(geom_means)
    return matrix, weights

# ==========================================
# HTML 網頁樣板 (Templates)
# ==========================================
INDEX_HTML = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>AHP 最佳橋型決策系統</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
<div class="container py-5">
    <h1 class="text-center mb-4">最佳橋型決策系統 (AHP)</h1>
    <form method="POST" class="bg-white p-4 rounded shadow-sm">
        <h4 class="mb-3 text-primary">第一步：建立主準則與子準則</h4>
        <p class="text-muted">您可以建立至多 3 個主準則，每個主準則可包含至多 5 個子準則。未填寫的欄位將自動忽略。</p>
        <div class="row">
        {% for i in range(1, 4) %}
            <div class="col-md-4 mb-4">
                <div class="card h-100">
                    <div class="card-header bg-secondary text-white fw-bold">主準則 {{ i }}</div>
                    <div class="card-body">
                        <input type="text" name="main_{{ i }}" class="form-control mb-3" placeholder="請輸入主準則名稱">
                        {% for j in range(1, 6) %}
                            <input type="text" name="sub_{{ i }}_{{ j }}" class="form-control mb-2 form-control-sm" placeholder="子準則 {{ j }}">
                        {% endfor %}
                    </div>
                </div>
            </div>
        {% endfor %}
        </div>
        <hr class="my-4">
        <h4 class="mb-3 text-success">第二步：建立評估方案</h4>
        <div class="row mb-4">
        {% for i in range(1, 6) %}
            <div class="col-md-2 mb-2">
                <input type="text" name="alt_{{ i }}" class="form-control" placeholder="方案 {{ i }}">
            </div>
        {% endfor %}
        </div>
        <button type="submit" class="btn btn-primary w-100 fs-5">下一步：進行兩兩比較</button>
    </form>
</div>
</body>
</html>
"""

COMPARE_HTML = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>兩兩比較 - AHP 最佳橋型決策系統</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
<div class="container py-5">
    <h2 class="mb-4">各階層重要程度兩兩比較</h2>
    <form method="POST" class="bg-white p-4 rounded shadow-sm">
        
        {% if main_criteria|length > 1 %}
        <h4 class="text-primary mb-3">主準則兩兩比較</h4>
        <div class="mb-4">
        {% for i in range(main_criteria|length) %}
            {% for j in range(i+1, main_criteria|length) %}
                <div class="row align-items-center mb-2">
                    <div class="col-md-6 text-end">
                        當 <strong>【{{ main_criteria[i] }}】</strong> 與 <strong>【{{ main_criteria[j] }}】</strong> 相較時，其重要性如何?
                    </div>
                    <div class="col-md-4">
                        <select name="main_{{ i }}_{{ j }}" class="form-select">
                            <option value="1">1 (同等重要)</option>
                            <option value="3">3 (較重要)</option>
                            <option value="5">5 (非常重要)</option>
                            <option value="1/3">1/3 (較不重要)</option>
                            <option value="1/5">1/5 (非常不重要)</option>
                        </select>
                    </div>
                </div>
            {% endfor %}
        {% endfor %}
        </div>
        <hr>
        {% endif %}

        {% for m_idx in range(main_criteria|length) %}
            {% set m = main_criteria[m_idx] %}
            {% set subs = hierarchy_data[m] %}
            {% if subs|length > 1 %}
            <h4 class="text-info mb-3">主準則【{{ m }}】下的子準則比較</h4>
            <div class="mb-4">
            {% for i in range(subs|length) %}
                {% for j in range(i+1, subs|length) %}
                    <div class="row align-items-center mb-2">
                        <div class="col-md-6 text-end">
                            當 <strong>【{{ subs[i] }}】</strong> 與 <strong>【{{ subs[j] }}】</strong> 相較時，其重要性如何?
                        </div>
                        <div class="col-md-4">
                            <select name="sub_{{ m_idx }}_{{ i }}_{{ j }}" class="form-select">
                                <option value="1">1 (同等重要)</option>
                                <option value="3">3 (較重要)</option>
                                <option value="5">5 (非常重要)</option>
                                <option value="1/3">1/3 (較不重要)</option>
                                <option value="1/5">1/5 (非常不重要)</option>
                            </select>
                        </div>
                    </div>
                {% endfor %}
            {% endfor %}
            </div>
            <hr>
            {% endif %}
        {% endfor %}

        {% if alternatives|length > 1 %}
        <h4 class="text-success mb-3">方案兩兩比較</h4>
        {% set ns = namespace(s_idx=0) %}
        {% for m in main_criteria %}
            {% for s in hierarchy_data[m] %}
                <h5 class="mt-4">針對子準則 <span class="badge bg-secondary">{{ s }}</span> 的方案比較</h5>
                <div class="mb-3 border-start border-3 border-success ps-3">
                {% for i in range(alternatives|length) %}
                    {% for j in range(i+1, alternatives|length) %}
                        <div class="row align-items-center mb-2">
                            <div class="col-md-6 text-end">
                                方案 <strong>【{{ alternatives[i] }}】</strong> 與 <strong>【{{ alternatives[j] }}】</strong> 相較時，其優勢如何?
                            </div>
                            <div class="col-md-4">
                                <select name="alt_{{ ns.s_idx }}_{{ i }}_{{ j }}" class="form-select">
                                    <option value="1">1 (同等優勢)</option>
                                    <option value="3">3 (較優越)</option>
                                    <option value="5">5 (非常優越)</option>
                                    <option value="1/3">1/3 (較劣勢)</option>
                                    <option value="1/5">1/5 (非常劣勢)</option>
                                </select>
                            </div>
                        </div>
                    {% endfor %}
                {% endfor %}
                </div>
                {% set ns.s_idx = ns.s_idx + 1 %}
            {% endfor %}
        {% endfor %}
        {% endif %}
        <div class="text-center mt-5">
            <button type="submit" class="btn btn-primary btn-lg px-5">計算決策結果</button>
        </div>
    </form>
</div>
</body>
</html>
"""

RESULT_HTML = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>決策結果 - AHP 最佳橋型決策系統</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
<div class="container py-5">
    <div class="bg-white p-5 rounded shadow">
        <h1 class="text-center mb-4 text-primary">最佳方案決策結果</h1>
        
        {% if best_alt %}
        <div class="alert alert-success text-center mb-5 border-success">
            <h2 class="mb-0">🏆 分析後橋梁最佳方案應為 <strong>{{ best_alt }}</strong></h2>
        </div>
        <h4 class="text-dark mb-3">主要勝出原因（得分貢獻最高的兩項子準則）：</h4>
        <ul class="list-group mb-5">
        {% for s_name, score_contrib in best_reasons %}
            <li class="list-group-item list-group-item-info">
                該方案在【<strong>{{ s_name }}</strong>】的評估中取得較高優勢 
                <span class="badge bg-success float-end mt-1">對總分貢獻: {{ "%.4f"|format(score_contrib) }}</span>
            </li>
        {% endfor %}
        </ul>
        {% endif %}

        <h4 class="mb-3 border-bottom pb-2">各方案總得分與排名</h4>
        <table class="table table-hover mb-5">
            <thead class="table-light"><tr><th>排名</th><th>方案名稱</th><th>總得分</th></tr></thead>
            <tbody>
            {% for name, score in sorted_alternatives %}
                <tr class="{% if loop.first %}table-warning fw-bold{% endif %}">
                    <td>第 {{ loop.index }} 名</td><td>{{ name }}</td><td>{{ "%.4f"|format(score) }}</td>
                </tr>
            {% endfor %}
            </tbody>
        </table>
        <div class="text-center"><a href="/" class="btn btn-outline-secondary px-4">重新評估</a></div>
    </div>
</div>
</body>
</html>
"""

# ==========================================
# 網頁路由 (Routes)
# ==========================================
@app.route('/', methods=['GET', 'POST'])
def index():
    """首頁：收集名稱資料"""
    if request.method == 'POST':
        main_criteria, hierarchy_data, alternatives = [], {}, []
        for i in range(1, 4):
            m_name = request.form.get(f'main_{i}', '').strip()
            if m_name:
                main_criteria.append(m_name)
                subs = [request.form.get(f'sub_{i}_{j}', '').strip() for j in range(1, 6) if request.form.get(f'sub_{i}_{j}', '').strip()]
                hierarchy_data[m_name] = subs if subs else [m_name + " (整體)"] # 防呆：無子準則時自動補上
                
        alternatives = [request.form.get(f'alt_{i}', '').strip() for i in range(1, 6) if request.form.get(f'alt_{i}', '').strip()]
        
        # 防呆處理：確保至少有預設資料
        if not main_criteria: main_criteria, hierarchy_data = ["預設主準則"], {"預設主準則": ["預設子準則"]}
        if not alternatives: alternatives = ["預設方案 A"]
            
        session['main_criteria'], session['hierarchy_data'], session['alternatives'] = main_criteria, hierarchy_data, alternatives
        return redirect(url_for('compare'))
        
    return render_template_string(INDEX_HTML)

@app.route('/compare', methods=['GET', 'POST'])
def compare():
    """比較頁面：收集矩陣資料"""
    main_criteria = session.get('main_criteria', [])
    hierarchy_data = session.get('hierarchy_data', {})
    alternatives = session.get('alternatives', [])
    
    if request.method == 'POST':
        session['main_comps'] = {f"{i}_{j}": request.form.get(f"main_{i}_{j}", "1") for i in range(len(main_criteria)) for j in range(i+1, len(main_criteria))}
        session['sub_comps'] = {str(m_idx): {f"{i}_{j}": request.form.get(f"sub_{m_idx}_{i}_{j}", "1") for i in range(len(hierarchy_data[m])) for j in range(i+1, len(hierarchy_data[m]))} for m_idx, m in enumerate(main_criteria)}
        all_subs = [s for m in main_criteria for s in hierarchy_data[m]]
        session['alt_comps'] = {str(s_idx): {f"{i}_{j}": request.form.get(f"alt_{s_idx}_{i}_{j}", "1") for i in range(len(alternatives)) for j in range(i+1, len(alternatives))} for s_idx in range(len(all_subs))}
        return redirect(url_for('result'))
        
    return render_template_string(COMPARE_HTML, hierarchy_data=hierarchy_data, main_criteria=main_criteria, alternatives=alternatives)

@app.route('/result')
def result():
    """結果頁面：計算與排名"""
    main_c, h_data, alts = session.get('main_criteria', []), session.get('hierarchy_data', {}), session.get('alternatives', [])
    _, main_w = calculate_weights_by_idx(len(main_c), session.get('main_comps', {}))
    global_weights, all_subs = {}, []
    for m_idx, m in enumerate(main_c):
        _, sub_w = calculate_weights_by_idx(len(h_data[m]), session.get('sub_comps', {}).get(str(m_idx), {}))
        for i, s in enumerate(h_data[m]):
            all_subs.append(s)
            global_weights[s] = (main_w[m_idx] if len(main_c) > 1 else 1.0) * (sub_w[i] if len(h_data[m]) > 1 else 1.0)
            
    final_scores, contributions = {alt: 0.0 for alt in alts}, {alt: {} for alt in alts}
    for s_idx, s in enumerate(all_subs):
        _, alt_w = calculate_weights_by_idx(len(alts), session.get('alt_comps', {}).get(str(s_idx), {}))
        for i, alt in enumerate(alts):
            contrib = (alt_w[i] if len(alts) > 1 else 1.0) * global_weights[s]
            final_scores[alt] += contrib
            contributions[alt][s] = contrib
            
    sorted_alts = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
    best_alt = sorted_alts[0][0] if sorted_alts else None
    best_reasons = sorted(contributions[best_alt].items(), key=lambda x: x[1], reverse=True)[:2] if best_alt else []
    
    return render_template_string(RESULT_HTML, sorted_alternatives=sorted_alts, best_alt=best_alt, best_reasons=best_reasons)

if __name__ == "__main__":
    # 啟動網頁伺服器
    app.run(debug=True, port=5000)
