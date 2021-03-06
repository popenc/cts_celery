:: Runs celery workers for p-chem calculators for development mode
:: Jun. 2016; np

:: Filename for .env to use when running celery workers:

rem echo .env Filename
rem echo env_filename

rem start celery -A tasks worker -Q manager --loglevel=info --concurrency=1 -n manager_worker
rem start celery -A tasks worker -Q chemaxon --loglevel=info --concurrency=1 -n chemaxon_worker
rem start celery -A tasks worker -Q metabolizer --loglevel=info --concurrency=1 -n metabolizer_worker
rem start celery -A tasks worker -Q cheminfo --loglevel=info --concurrency=1 -n cheminfo_worker
rem start celery -A tasks worker -Q sparc --loglevel=info --concurrency=1 -n sparc_worker
rem start celery -A tasks worker -Q epi --loglevel=info --concurrency=1 -n epi_worker
rem start celery -A tasks worker -Q measured --loglevel=info --concurrency=1 -n measured_worker
rem start celery -A tasks worker -Q test --loglevel=info --concurrency=1 -n test_worker

start celery -A tasks worker -Q manager_queue --loglevel=info --concurrency=1 -n manager_worker
start celery -A tasks worker -Q cts_queue --loglevel=info --concurrency=1 -n cts_worker_1
rem start celery -A tasks worker -Q cts_queue --loglevel=info --concurrency=1 -n cts_worker_2
rem start celery -A tasks worker -Q cts_queue --loglevel=info --concurrency=1 -n cts_worker_3

:: Below is the little servlet to monitor celery workers. It's not required.
:: start flower -A tasks --port=5000