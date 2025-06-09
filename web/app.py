import os
import pandas as pd
from flask import Flask, render_template, request, jsonify
import joblib
from datetime import datetime
import calendar
import numpy as np
import re
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import LabelEncoder
from sklearn.cluster import KMeans
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
# Không cần StandardScaler vì đã loại bỏ

app = Flask(__name__)

# Định nghĩa đường dẫn đến thư mục 'modeling'
# Đảm bảo đường dẫn này chính xác so với vị trí của app.py
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MODELING_PATH = os.path.join(PROJECT_ROOT, 'modeling')
PREPROCESSING_PATH = os.path.join(PROJECT_ROOT, 'preprocessing')

# Load tidy_data.csv globally and normalize the 'name' column
try:
    TIDY_DATA = pd.read_csv(os.path.join(PREPROCESSING_PATH, 'tidy_data.csv'), encoding='utf-8-sig')
    TIDY_DATA['normalized_name'] = TIDY_DATA['name'].astype(str).str.lower().str.strip()
    print("tidy_data.csv loaded and normalized successfully.")
except FileNotFoundError as e:
    print(f"Error loading tidy_data.csv: {e}")
    print("Please ensure tidy_data.csv is in the 'preprocessing/' directory.")
    exit()

# --- 1. Định nghĩa lại các Custom Transformers (Đảm bảo giống hệt trong modeling.ipynb) ---
class Dropper(BaseEstimator, TransformerMixin):
    def __init__(self, columns):
        self.columns = columns

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X.drop(columns=self.columns, errors='ignore').copy()

class DateTimeFeaturesTransformer(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X_copy = X.copy()
        X_copy['time'] = pd.to_datetime(X_copy['time'], errors='coerce')
        X_copy['time_difference'] = (datetime.now() - X_copy['time']).dt.days

        current_date_for_warranty = datetime.now()
        warranty_processed_list = []

        for item in X_copy['warranty']:
            if pd.isna(item):
                warranty_processed_list.append(np.nan)
                continue
            item_str = str(item).strip()
            if "tháng" in item_str:
                num_months_str = item_str.replace("tháng", "").strip()
                try:
                    num_months = int(num_months_str)
                except ValueError:
                    warranty_processed_list.append(np.nan)
                    continue
                year = current_date_for_warranty.year
                month = current_date_for_warranty.month + num_months
                day = current_date_for_warranty.day
                while month > 12:
                    month -= 12
                    year += 1       
                try:
                    new_date = datetime(year, month, day)
                except ValueError:
                    last_day_of_month = calendar.monthrange(year, month)[1]
                    new_date = datetime(year, month, last_day_of_month)
                warranty_processed_list.append(new_date)
            else:
                try:
                    warranty_processed_list.append(datetime.strptime(item_str, "%d/%m/%Y"))
                except ValueError:
                    warranty_processed_list.append(np.nan)
        
        X_copy['warranty_processed'] = warranty_processed_list
        current_date_series = pd.Series([current_date_for_warranty] * len(X_copy), index=X_copy.index)
        time_remaining = X_copy['warranty_processed'] - current_date_series
        X_copy['day_remaining_warranty'] = time_remaining.dt.days + 1
        
        return X_copy.copy() 

class OperatingSystemTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, encoder):
        self.encoder = encoder

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X_copy = X.copy()
        def map_os_family(os_val):
            if pd.isnull(os_val):
                return 'Unknown'
            os_val = os_val.lower()
            if 'ios' in os_val: return 'iOS'
            elif 'android' in os_val: return 'Android'
            elif 'coloros' in os_val: return 'Android'
            elif 'miui' in os_val: return 'Android'
            elif 'hyperos' in os_val: return 'Android'
            elif 'funtouch' in os_val: return 'Android'
            elif 'oxygenos' in os_val: return 'Android'
            elif 'realme ui' in os_val: return 'Android'
            elif 'xos' in os_val: return 'Android'
            elif 'mocor' in os_val: return 'Android'
            elif 'series 30' in os_val or 's30' in os_val: return 'Feature OS'
            else: return 'Other'
        
        X_copy['os'] = X_copy['operating_system'].apply(map_os_family)
        os_mapping = {label: idx for idx, label in enumerate(self.encoder.classes_)}
        X_copy['os'] = X_copy['os'].map(os_mapping).fillna(-1).astype(int)
        return X_copy.copy() 

class CPUTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, encoder):
        self.encoder = encoder

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X_copy = X.copy()
        X_copy['chip'] = X_copy['CPU'].str.extract(r'(Apple|Snapdragon|MediaTek|Exynos|Unisoc)', expand=False)
        cpu_mapping = {label: idx for idx, label in enumerate(self.encoder.classes_)}
        X_copy['chip'] = X_copy['chip'].fillna('Unknown').map(cpu_mapping).fillna(-1).astype(int)
        return X_copy.copy() 

class ConditionTransformer(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X_copy = X.copy()
        condition_mapping = {'Cũ trầy xước cấn': 0, 'Cũ trầy xước': 1, 'Cũ': 2, 'Cũ đẹp': 3}
        X_copy['condition'] = X_copy['condition'].map(condition_mapping).fillna(np.nan)
        return X_copy.copy()

class BrandTransformer(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X_copy = X.copy()
        brand_mapping = {
            'apple': 3, 'samsung': 3,
            'honor': 2, 'oppo': 2, 'xiaomi': 2, 'vivo': 2,
            'realme': 1, 'tecno': 1, 'nokia': 1, 'tcl': 1,
            'mobell': 0, 'viettel': 0, 'masstel': 0
        }
        X_copy['brand'] = X_copy['brand'].str.lower().map(brand_mapping).fillna(np.nan)
        return X_copy.copy()

class NameEncoder(BaseEstimator, TransformerMixin):
    def __init__(self, encoder):
        self.encoder = encoder

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X_copy = X.copy()
        # Ensure name is string, lowercased, and stripped
        X_copy['name'] = X_copy['name'].astype(str).str.lower().str.strip()
        mapping = {label: idx for idx, label in enumerate(self.encoder.classes_)}
        X_copy['name'] = X_copy['name'].map(mapping).fillna(-1).astype(int)
        return X_copy.copy()

class GPUTransformer(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X_copy = X.copy()
        high_cond = X_copy['GPU'].str.lower().str.contains(
            'adreno-7|adreno-8|mali-g7|mali-g76|mali-g77|mali-g78|apple-gpu 6|apple-gpu 5|immortalis|xclipse|powervr-series7xt', na=False)
        low_cond = X_copy['GPU'].str.lower().str.contains(
            'adreno-6|adreno-5|adreno-4|mali-g6|mali-g57|mali-g68|mali-g52|powervr-ge8320|xclipse-920|apple-gpu 4|adreno-619|adreno-644|adreno-670', na=False)
        no_gpu_cond = X_copy['GPU'].isna() | (X_copy['GPU'].str.lower() == 'unknown')
        conditions = [no_gpu_cond, high_cond, low_cond]
        choices = ['0', '2', '1']
        X_copy['GPU'] = np.select(conditions, choices, default='1')
        X_copy['GPU'] = pd.to_numeric(X_copy['GPU'], errors='coerce')
        return X_copy.copy()

class BluetoothTransformer(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X_copy = X.copy()
        version_score_map = {
            '2.1': 1.0, '4.2': 2.0, '5.0': 3.0, '5.1': 3.2, '5.2': 3.4, '5.3': 3.6, '5.4': 3.8, '6.0': 4.0
        }
        profile_points = {
            'apt-X Adaptive': 0.2, 'apt-X HD': 0.15, 'LHDC': 0.15, 'apt-X': 0.1, 'A2DP': 0.1, 'LE': 0.1, 'BLE': 0.05
        }
        def encode_bluetooth_weighted(bluetooth_str):
            if pd.isna(bluetooth_str):
                return np.nan
            version_match = re.findall(r'v(\d\.\d)', bluetooth_str)
            version = version_score_map.get(version_match[0], 0) if version_match else 0
            profile_score = sum(pt for profile, pt in profile_points.items() if profile in bluetooth_str)
            return round(version + profile_score, 2)
        X_copy['bluetooth'] = X_copy['bluetooth'].apply(encode_bluetooth_weighted)
        return X_copy.copy()

class PriceNewTransformer(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        X_copy = X.copy()
        if 'price_new' in X_copy.columns:
            X_copy['price_new'] = X_copy['price_new'].fillna(0) / 1000 
        return X_copy.copy()

class KMeansClusterTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, kmeans_model, feature_names_at_imputer_stage=None):
        self.kmeans_model = kmeans_model
        self.feature_names_at_imputer_stage = feature_names_at_imputer_stage 

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        if self.feature_names_at_imputer_stage is None:
            raise ValueError("KMeansClusterTransformer requires 'feature_names_at_imputer_stage' to be set in its constructor.")
        
        if not isinstance(X, pd.DataFrame):
            X_df_reconstructed = pd.DataFrame(X, columns=self.feature_names_at_imputer_stage)
        else:
            X_df_reconstructed = X.copy()

        kmeans_expected_features = self.kmeans_model.feature_names_in_ if hasattr(self.kmeans_model, 'feature_names_in_') else self.feature_names_at_imputer_stage

        for col in kmeans_expected_features:
            if col not in X_df_reconstructed.columns:
                X_df_reconstructed[col] = 0

        X_cluster = X_df_reconstructed[kmeans_expected_features].fillna(0).copy()
        
        X_df_reconstructed['Cluster'] = self.kmeans_model.predict(X_cluster)
        
        return X_df_reconstructed.copy()

# Hàm hỗ trợ cho OperatingSystemTransformer
def map_os_family(os_val):
    if pd.isnull(os_val):
        return 'Unknown'
    os_val = os_val.lower()
    if 'ios' in os_val: return 'iOS'
    elif 'android' in os_val: return 'Android'
    elif 'coloros' in os_val: return 'Android'
    elif 'miui' in os_val: return 'Android'
    elif 'hyperos' in os_val: return 'Android'
    elif 'funtouch' in os_val: return 'Android'
    elif 'oxygenos' in os_val: return 'Android'
    elif 'realme ui' in os_val: return 'Android'
    elif 'xos' in os_val: return 'Android'
    elif 'mocor' in os_val: return 'Android'
    elif 'series 30' in os_val or 's30' in os_val: return 'Feature OS'
    else: return 'Other'

# --- Tải các Encoder và KMeans Model ---
try:
    os_encoder = joblib.load(os.path.join(MODELING_PATH, 'os_label_encoder.pkl'))
    cpu_encoder = joblib.load(os.path.join(MODELING_PATH, 'cpu_label_encoder.pkl'))
    name_encoder = joblib.load(os.path.join(MODELING_PATH, 'name_label_encoder.pkl'))
    kmeans_model = joblib.load(os.path.join(MODELING_PATH, 'kmeans_model.pkl'))
    prediction_pipeline = joblib.load(os.path.join(MODELING_PATH, 'prediction_pipeline.pkl'))
    lgbm_model = joblib.load(os.path.join(MODELING_PATH, 'lgbm_model.pkl')) # Tải mô hình của bạn
    print("All models and pipeline loaded successfully.")
except FileNotFoundError as e:
    print(f"Error loading model files: {e}")
    print("Please ensure modeling.ipynb has been run and all .pkl files are in the 'modeling/' directory.")
    exit()

@app.route('/')
def home():
    # Lấy danh sách tên máy duy nhất đã chuẩn hóa từ TIDY_DATA
    # Sắp xếp để hiển thị trong dropdown một cách có tổ chức
    unique_names = sorted(TIDY_DATA['name'].astype(str).str.strip().unique().tolist())
    
    # Các tùy chọn cho tình trạng
    conditions = ['Cũ trầy xước cấn', 'Cũ trầy xước', 'Cũ', 'Cũ đẹp']
    
    return render_template('index.html', unique_names=unique_names, conditions=conditions)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        user_name_input = request.form['name']
        user_condition_input = request.form['condition']

        # Normalize user name input for robust matching
        normalized_user_name = user_name_input.lower().strip()

        # Find matching row in TIDY_DATA based on normalized name
        matching_rows = TIDY_DATA[TIDY_DATA['normalized_name'] == normalized_user_name]

        if not matching_rows.empty:
            base_info = matching_rows.iloc[0].to_dict()
        else:
            # Fallback to the first row if name not found
            # Use the first row from TIDY_DATA for default values
            base_info = TIDY_DATA.iloc[0].to_dict()
            print(f"Warning: Name '{user_name_input}' not found in tidy_data.csv. Using default row.")

        # Get initial columns from TIDY_DATA, excluding target and helper columns
        # This list ensures the DataFrame created matches the input to the pipeline's fit method
        expected_raw_columns = TIDY_DATA.columns.tolist()
        if 'price_old' in expected_raw_columns:
            expected_raw_columns.remove('price_old')
        if 'normalized_name' in expected_raw_columns:
            expected_raw_columns.remove('normalized_name')
        
        # Construct phone_info dictionary by getting values from base_info for all expected columns
        # Fill with None if a column is missing from base_info (shouldn't happen if TIDY_DATA is complete)
        phone_info = {col: base_info.get(col) for col in expected_raw_columns}

        # Override with user inputs for 'name' and 'condition'
        phone_info['name'] = user_name_input # Keep original user input for 'name' in this dictionary
        phone_info['condition'] = user_condition_input

        # Explicitly ensure types for numeric fields (handle None/NaN from base_info)
        # The `or 0` handles cases where .get() might return None.
        phone_info['price_new'] = float(phone_info.get('price_new', 0) or 0) 
        phone_info['RAM'] = float(phone_info.get('RAM', 0) or 0)
        phone_info['capacity'] = float(phone_info.get('capacity', 0) or 0)
        phone_info['battery'] = float(phone_info.get('battery', 0) or 0)
        phone_info['screen_size'] = float(phone_info.get('screen_size', 0) or 0)
        phone_info['weight'] = float(phone_info.get('weight', 0) or 0)
        phone_info['refresh_rate'] = float(phone_info.get('refresh_rate', 0) or 0)
        phone_info['resolution_height'] = float(phone_info.get('resolution_height', 0) or 0)
        phone_info['resolution_width'] = float(phone_info.get('resolution_width', 0) or 0)
        # Ensure has_esim is an integer
        phone_info['has_esim'] = int(phone_info.get('has_esim', 0) or 0) 
        phone_info['height'] = float(phone_info.get('height', 0) or 0)
        phone_info['width'] = float(phone_info.get('width', 0) or 0)
        phone_info['depth'] = float(phone_info.get('depth', 0) or 0)

        # Handle 'time' and 'warranty' - convert pd.Timestamp to string if present, or set default string
        if isinstance(phone_info.get('time'), pd.Timestamp):
            phone_info['time'] = phone_info['time'].strftime('%Y-%m-%d')
        elif phone_info.get('time') is None: 
            phone_info['time'] = datetime.now().strftime('%Y-%m-%d') # Default to current date string
        
        if isinstance(phone_info.get('warranty'), pd.Timestamp):
            phone_info['warranty'] = phone_info['warranty'].strftime('%d/%m/%Y')
        elif phone_info.get('warranty') is None: 
            phone_info['warranty'] = "0 tháng" # Default to '0 tháng' string

        # Convert potentially non-string types to string for transformer methods, ensuring 'unknown' fallback
        # .get() with None as default, then convert to string if not None, else 'unknown'
        phone_info['GPU'] = str(phone_info.get('GPU')) if phone_info.get('GPU') is not None else 'unknown'
        phone_info['bluetooth'] = str(phone_info.get('bluetooth')) if phone_info.get('bluetooth') is not None else 'unknown'
        phone_info['operating_system'] = str(phone_info.get('operating_system')) if phone_info.get('operating_system') is not None else 'unknown'
        phone_info['CPU'] = str(phone_info.get('CPU')) if phone_info.get('CPU') is not None else 'unknown'
        phone_info['display_technology'] = str(phone_info.get('display_technology')) if phone_info.get('display_technology') is not None else 'unknown'
        phone_info['color'] = str(phone_info.get('color')) if phone_info.get('color') is not None else 'unknown'
        phone_info['brand'] = str(phone_info.get('brand')) if phone_info.get('brand') is not None else 'unknown' 
        phone_info['image'] = str(phone_info.get('image')) if phone_info.get('image') is not None else '' # Add image with default empty string

        # Create DataFrame from phone_info dictionary, explicitly passing expected columns
        input_data_for_pipeline = pd.DataFrame([phone_info], columns=expected_raw_columns)

        # Preprocess input data using the loaded pipeline
        processed_input_data = prediction_pipeline.transform(input_data_for_pipeline)

        # Predict price using the loaded model
        predicted_price_thousand_vnd = lgbm_model.predict(processed_input_data)[0]

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
    app.run(debug=True)
