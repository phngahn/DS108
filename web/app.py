from flask import Flask, request, jsonify, render_template
import pandas as pd
import numpy as np
import joblib
from datetime import datetime
import calendar
import re
from sklearn.base import BaseEstimator, TransformerMixin
import os

app = Flask(__name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MODELING_PATH = os.path.join(PROJECT_ROOT, 'modeling')
PREPROCESSING_PATH = os.path.join(PROJECT_ROOT, 'preprocessing')

try:
    TIDY_DATA = pd.read_csv(os.path.join(PREPROCESSING_PATH, 'tidy_data.csv'), encoding='utf-8-sig')
    TIDY_DATA['normalized_name'] = TIDY_DATA['name'].astype(str).str.lower().str.strip()
    print("tidy_data.csv loaded and normalized successfully.")
except FileNotFoundError as e:
    print(f"Error loading tidy_data.csv: {e}")
    print("Vui lòng đảm bảo tidy_data.csv có trong thư mục 'preprocessing/' của dự án.")
    exit()

class Dropper(BaseEstimator, TransformerMixin):
    def __init__(self, columns): self.columns = columns
    def fit(self, X, y=None): return self
    def transform(self, X): return X.drop(columns=self.columns, errors='ignore').copy()

class DateTimeFeaturesTransformer(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None): return self
    def transform(self, X):
        X_copy = X.copy()
        X_copy['time'] = pd.to_datetime(X_copy['time'], errors='coerce')
        X_copy['time_difference'] = (datetime.now() - X_copy['time']).dt.days

        current_date_for_warranty = datetime.now()
        warranty_processed_list = []
        for item in X_copy['warranty']:
            if pd.isna(item): warranty_processed_list.append(np.nan); continue
            item_str = str(item).strip()
            if "tháng" in item_str:
                num_months_str = item_str.replace("tháng", "").strip()
                try: num_months = int(num_months_str)
                except ValueError: warranty_processed_list.append(np.nan); continue
                year = current_date_for_warranty.year
                month = current_date_for_warranty.month + num_months
                day = current_date_for_warranty.day
                while month > 12: month -= 12; year += 1
                try: new_date = datetime(year, month, day)
                except ValueError: last_day_of_month = calendar.monthrange(year, month)[1]; new_date = datetime(year, month, last_day_of_month)
                warranty_processed_list.append(new_date)
            else:
                try: warranty_processed_list.append(datetime.strptime(item_str, "%d/%m/%Y"))
                except ValueError: warranty_processed_list.append(np.nan)
        X_copy['warranty_processed'] = warranty_processed_list
        current_date_series = pd.Series([current_date_for_warranty] * len(X_copy), index=X_copy.index)
        time_remaining = X_copy['warranty_processed'] - current_date_series
        X_copy['day_remaining_warranty'] = time_remaining.dt.days + 1
        return X_copy.copy()

class OperatingSystemTransformer(BaseEstimator, TransformerMixin):
    def __init__(self): self.mean_score = None
    def get_update_score(self, os_name):
        if pd.isnull(os_name): return np.nan
        if os_name.startswith("iOS"):
            match = re.search(r"iOS\s*(\d+)", os_name); return int(match.group(1)) / 18 if match else np.nan
        elif os_name.startswith("Android"):
            match = re.search(r"Android\s*(\d+)", os_name); return int(match.group(1)) / 15 if match else np.nan
        return np.nan
    def fit(self, X, y=None): self.mean_score = X['operating_system'].apply(self.get_update_score).mean(); return self
    def transform(self, X): X_copy = X.copy(); X_copy['operating_system'] = X_copy['operating_system'].apply(self.get_update_score); X_copy['operating_system'].fillna(self.mean_score, inplace=True); return X_copy

class CPUTransformer(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None): return self
    def transform(self, X):
        X_copy = X.copy()
        high_pattern = re.compile(r'(?i)(?:a18|a17|a16|a15(?:\sbionic)?|snapdragon\s8(?:\sgen\s3|\sgen\s2|\+?\sgen\s1)|8\selite|exynos\s2400(?:e)?|exynos\s2200|dimensity\s(?:9300\+|9400|9200|8300))')
        mid_pattern = re.compile(r'(?i)(?:a14(?:\sbionic)?|a13(?:\sbionic)?|snapdragon\s(?:7(?:\sgen\s[13]|s\sgen\s2)|6\sgen\s[134]|6s\s(?:gen\s1|4g\sgen\s1))|exynos\s(?:2100|15[80]|14[80]|13[80]|1280)|dimensity\s(?:1080|7050|7025|7300|6300|6100\+|6020|700|8350|d6300))')
        low_pattern = re.compile(r'(?i)(?:snapdragon\s(?:6[895]|680(?:\s4g)?|sm6225)|helio\s(?:g(?:99|96|92|91|88|85|81|36|35)|p35|g100)|mt6762|unisoc\s(?:t(?:7250|7225|615|612|606|107)|ums9117)|tiger\s?t693)')
        def classify_cpu(cpu):
            if pd.isnull(cpu): return 1
            cpu = str(cpu).strip()
            if high_pattern.search(cpu): return 3
            elif mid_pattern.search(cpu): return 2
            elif low_pattern.search(cpu): return 1
            else: return 1
        X_copy['CPU'] = X_copy['CPU'].apply(classify_cpu).astype(int)
        return X_copy

class ConditionTransformer(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None): return self
    def transform(self, X):
        X_copy = X.copy()
        condition_mapping = {'Cũ trầy xước cấn': 1, 'Cũ trầy xước': 2, 'Cũ': 3, 'Cũ đẹp': 4}
        X_copy['condition'] = X_copy['condition'].map(condition_mapping).fillna(np.nan)
        return X_copy.copy()

class BrandTransformer(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None): return self
    def transform(self, X):
        X_copy = X.copy()
        brand_mapping = {'apple': 4, 'samsung': 4,'honor': 3, 'oppo': 3, 'xiaomi': 3, 'vivo': 3,'realme': 2, 'tecno': 2, 'nokia': 2, 'tcl': 2,'mobell': 1, 'viettel': 1, 'masstel': 1}
        X_copy['brand'] = X_copy['brand'].str.lower().map(brand_mapping).fillna(np.nan)
        return X_copy.copy()

class NameEncoder(BaseEstimator, TransformerMixin):
    def __init__(self, encoder): self.encoder = encoder
    def fit(self, X, y=None): return self
    def transform(self, X):
        X_copy = X.copy()
        mapping = {label: idx for idx, label in enumerate(self.encoder.classes_)}
        X_copy['name'] = X_copy['name'].map(mapping).fillna(-1).astype(int)
        return X_copy.copy()

class GPUTransformer(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None): return self
    def transform(self, X):
        X_copy = X.copy()
        high_cond = X_copy['GPU'].str.lower().str.contains('adreno-7|adreno-8|mali-g7|mali-g76|mali-g77|mali-g78|apple-gpu 6|apple-gpu 5|immortalis|xclipse|powervr-series7xt', na=False)
        low_cond = X_copy['GPU'].str.lower().str.contains('adreno-6|adreno-5|adreno-4|mali-g6|mali-g57|mali-g68|mali-g52|powervr-ge8320|xclipse-920|apple-gpu 4|adreno-619|adreno-644|adreno-670', na=False)
        no_gpu_cond = X_copy['GPU'].isna() | (X_copy['GPU'].str.lower() == 'unknown')
        conditions = [no_gpu_cond, high_cond, low_cond]
        choices = ['1', '3', '2']
        X_copy['GPU'] = np.select(conditions, choices, default='1')
        X_copy['GPU'] = pd.to_numeric(X_copy['GPU'], errors='coerce')
        return X_copy.copy()

class BluetoothTransformer(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None): return self
    def transform(self, X):
        X_copy = X.copy()
        version_score_map = {'2.1': 1.0, '4.2': 2.0, '5.0': 3.0, '5.1': 3.2, '5.2': 3.4, '5.3': 3.6, '5.4': 3.8, '6.0': 4.0}
        profile_points = {'apt-X Adaptive': 0.2, 'apt-X HD': 0.15, 'LHDC': 0.15, 'apt-X': 0.1, 'A2DP': 0.1, 'LE': 0.1, 'BLE': 0.05}
        def encode_bluetooth_weighted(bluetooth_str):
            if pd.isna(bluetooth_str): return np.nan
            version_match = re.findall(r'v(\d\.\d)', bluetooth_str)
            version = version_score_map.get(version_match[0], 0) if version_match else 0
            profile_score = sum(pt for profile, pt in profile_points.items() if profile in bluetooth_str)
            return round(version + profile_score, 2)
        X_copy['bluetooth'] = X_copy['bluetooth'].apply(encode_bluetooth_weighted)
        return X_copy.copy()

class PriceNewTransformer(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None): return self
    def transform(self, X):
        X_copy = X.copy()
        if 'price_new' in X_copy.columns: X_copy['price_new'] = X_copy['price_new'].fillna(0) / 1000
        return X_copy.copy()

class ScreenResolutionTrasformer(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None): return self
    def transform(self, X):
        X_copy = X.copy()
        if 'screen_resolution' in X_copy.columns:
            X_copy['screen_resolution'] = pd.to_numeric(X_copy['screen_resolution'], errors='coerce')
            X_copy['screen_resolution'] = X_copy['screen_resolution'].fillna(0) / 1000000
        return X_copy.copy()

class DisplayTechnologyTransformer(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None): return self
    def transform(self, X):
        X_copy = X.copy()
        LCD = X_copy['display_technology'].str.lower().str.contains('lcd|tn|liquid', na=False)
        OLED = X_copy['display_technology'].str.lower().str.contains('oled|amoled|super retina xdr', na=False)
        no_display_technology = X_copy['display_technology'].isna() | (X_copy['display_technology'].str.lower() == 'unknown')
        conditions = [no_display_technology, LCD, OLED]
        choices = ['1', '2', '3']
        X_copy['display_technology'] = np.select(conditions, choices, default='1')
        X_copy['display_technology'] = pd.to_numeric(X_copy['display_technology'], errors='coerce')
        return X_copy.copy()

class KMeansClusterTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, kmeans_model, feature_names_at_imputer_stage=None):
        self.kmeans_model = kmeans_model
        self.feature_names_at_imputer_stage = feature_names_at_imputer_stage
    def fit(self, X, y=None): return self
    def transform(self, X):
        if self.feature_names_at_imputer_stage is None: raise ValueError("KMeansClusterTransformer yêu cầu 'feature_names_at_imputer_stage' phải được thiết lập trong hàm tạo của nó.")
        X_df_reconstructed = pd.DataFrame(X, columns=self.feature_names_at_imputer_stage) if not isinstance(X, pd.DataFrame) else X.copy()
        kmeans_expected_features = self.kmeans_model.feature_names_in_ if hasattr(self.kmeans_model, 'feature_names_in_') else self.feature_names_at_imputer_stage
        for col in kmeans_expected_features:
            if col not in X_df_reconstructed.columns: X_df_reconstructed[col] = 0
        X_cluster = X_df_reconstructed[kmeans_expected_features].copy()
        X_df_reconstructed['Cluster'] = self.kmeans_model.predict(X_cluster)
        return X_df_reconstructed.copy()


try:
    prediction_pipeline = joblib.load(os.path.join(MODELING_PATH, 'prediction_pipeline.pkl'))
    print("Đã tải pipeline dự đoán thành công từ ../modeling/prediction_pipeline.pkl.")
except FileNotFoundError as e:
    print(f"Lỗi: Không tìm thấy file prediction_pipeline.pkl: {e}")
    print("Vui lòng đảm bảo file này đã được tạo và lưu trong thư mục 'modeling/' của dự án.")
    exit()

try:
    cb_model = joblib.load(os.path.join(MODELING_PATH, 'cb_model.pkl'))
    print("Đã tải mô hình CatBoost thành công từ ../modeling/cb_model.pkl.")
except FileNotFoundError as e:
    print(f"Lỗi: Không tìm thấy file cb_model.pkl: {e}")
    print("Vui lòng đảm bảo mô hình đã được huấn luyện và lưu trong thư mục 'modeling/'.")
    exit()

@app.route('/')
def home():
    unique_names = sorted(TIDY_DATA['name'].astype(str).str.strip().unique().tolist())
    conditions = ['Cũ trầy xước cấn', 'Cũ trầy xước', 'Cũ', 'Cũ đẹp']
    return render_template('index.html', unique_names=unique_names, conditions=conditions)


@app.route('/predict', methods=['POST'])
def predict():
    try:
        user_input_raw = request.get_json() 

        user_name_input = user_input_raw.get('name')
        user_condition_input = user_input_raw.get('condition')

        if not user_name_input or not user_condition_input:
            raise ValueError("Tên sản phẩm hoặc tình trạng không được để trống.")

        normalized_user_name = str(user_name_input).lower().strip()

        matching_rows = TIDY_DATA[TIDY_DATA['normalized_name'] == normalized_user_name]

        if not matching_rows.empty:
            base_info = matching_rows.iloc[0].to_dict()
        else:
            base_info = TIDY_DATA.iloc[0].to_dict()
            print(f"Warning: Name '{user_name_input}' not found in tidy_data.csv. Using default row.")
        
        expected_raw_columns = [col for col in TIDY_DATA.columns.tolist() if col not in ['price_old', 'normalized_name']]
        
        phone_info = {col: base_info.get(col) for col in expected_raw_columns}

        phone_info['name'] = user_name_input
        phone_info['condition'] = user_condition_input

        numeric_cols_default_zero = [
            'price_new', 'RAM', 'capacity', 'battery', 'screen_size', 'weight',
            'refresh_rate', 'resolution_height', 'resolution_width', 'has_esim',
            'height', 'width', 'depth', 'screen_resolution'
        ]
        for col in numeric_cols_default_zero:
            val = phone_info.get(col)
            try:
                phone_info[col] = float(val) if val is not None and val != '' else np.nan
            except (ValueError, TypeError):
                phone_info[col] = np.nan

        if isinstance(phone_info.get('time'), pd.Timestamp):
            phone_info['time'] = phone_info['time'].strftime('%Y-%m-%d')
        elif phone_info.get('time') is None or not str(phone_info.get('time')).strip():
            phone_info['time'] = datetime.now().strftime('%Y-%m-%d')
            
        if isinstance(phone_info.get('warranty'), pd.Timestamp):
            phone_info['warranty'] = phone_info['warranty'].strftime('%d/%m/%Y')
        elif phone_info.get('warranty') is None or not str(phone_info.get('warranty')).strip():
            phone_info['warranty'] = "0 tháng"

        for key in ['GPU', 'bluetooth', 'operating_system', 'CPU', 'display_technology', 'color', 'brand', 'image']:
            phone_info[key] = str(phone_info.get(key)) if phone_info.get(key) is not None else 'unknown'
            if phone_info[key].lower() == 'nan' or phone_info[key].lower() == '<na>':
                phone_info[key] = 'unknown'

        if phone_info['image'] == 'unknown':
            phone_info['image'] = ''

        input_data_for_pipeline = pd.DataFrame([phone_info], columns=expected_raw_columns)

        processed_input_data = prediction_pipeline.transform(input_data_for_pipeline)

        predicted_price_thousand_vnd = cb_model.predict(processed_input_data)[0]

        predicted_price_vnd = round(predicted_price_thousand_vnd * 1000)

        return jsonify({'predicted_price': f"{predicted_price_vnd:,.0f} đ"})

    except ValueError as ve:
        print(f"ValueError: {ve}")
        return jsonify({'error': f"Lỗi đầu vào dữ liệu: {ve}. Vui lòng kiểm tra lại các trường số."}), 400
    except KeyError as ke:
        print(f"KeyError: {ke}")
        return jsonify({'error': f"Lỗi trường dữ liệu bị thiếu hoặc không khớp: {ke}. Vui lòng đảm bảo tất cả các trường được điền đúng và tên cột khớp."}), 400
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({'error': f"Đã xảy ra lỗi không mong muốn: {e}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)