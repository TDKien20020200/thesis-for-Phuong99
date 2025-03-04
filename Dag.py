from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import os

# Thêm đường dẫn ChromeDriver vào PATH (nếu sử dụng Chrome WebDriver trên macOS)
# Điều chỉnh đường dẫn này dựa trên vị trí ChromeDriver của bạn
os.environ["PATH"] += os.pathsep + os.path.expanduser("~/.wdm/drivers/chromedriver/mac64/")

# Define default arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 6, 9),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=2),
}

# Define the DAG
dag = DAG(
    'stock_analysis_pipeline',
    default_args=default_args,
    description='A simple stock analysis DAG',
    schedule_interval=timedelta(days=1),
)

# Đường dẫn tới thư mục DAGs trên macOS (giả sử bạn chạy Airflow local)
DAG_DIR = os.path.expanduser("~/airflow/dags/")

# Define tasks using BashOperator
bctc_task = BashOperator(
    task_id='bctc_task',
    bash_command=f'python {DAG_DIR}CrawlBCTC.py',
    dag=dag,
)

crawl_news_task = BashOperator(
    task_id='crawl_news_task',
    bash_command=f'python {DAG_DIR}CrawlNews.py',
    dag=dag,
)

crawl_price_task = BashOperator(
    task_id='crawl_price_task',
    bash_command=f'python {DAG_DIR}CrawlPrice.py',
    dag=dag,
)

clustering_task = BashOperator(
    task_id='clustering_task',
    bash_command=f'python {DAG_DIR}Clustering.py',
    dag=dag,
)

chooseStock_task = BashOperator(
    task_id='chooseStock_task',
    bash_command=f'python {DAG_DIR}getinf.py',
    dag=dag,
)

# Define task dependencies
[crawl_news_task, crawl_price_task] >> bctc_task >> clustering_task >> chooseStock_task

if __name__ == "__main__":
    dag.cli()