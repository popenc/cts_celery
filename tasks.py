"""
CTS celery instance
"""
from __future__ import absolute_import
import os
from os.path import dirname, abspath
import sys
from celery import Celery
import logging
import redis
import json


logging.getLogger('celery.task.default').setLevel(logging.DEBUG)
logging.getLogger().setLevel(logging.DEBUG)


from temp_config.set_environment import DeployEnv
runtime_env = DeployEnv()
runtime_env.load_deployment_environment()



# if not os.environ.get('DJANGO_SETTINGS_FILE'):
#     os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qed_cts.settings_outside')
# else:
#     os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')



from cts_calcs.calculator_chemaxon import JchemCalc
from cts_calcs.calculator_sparc import SparcCalc
from cts_calcs.calculator_epi import EpiCalc
from cts_calcs.calculator_measured import MeasuredCalc
from cts_calcs.calculator_test import TestCalc
from cts_calcs.calculator_test import TestWSCalc
from cts_calcs.calculator_metabolizer import MetabolizerCalc
from cts_calcs.calculator import Calculator
from cts_calcs.chemical_information import ChemInfo
from celery.task.control import revoke



REDIS_HOSTNAME = os.environ.get('REDIS_HOSTNAME', 'localhost')
REDIS_PORT = os.environ.get('REDIS_PORT', 6379)

logging.info("REDIS_HOSTNAME: {}".format(REDIS_HOSTNAME))
logging.info("REDIS_PORT: {}".format(REDIS_PORT))

app = Celery('tasks',
				broker='redis://{}:6379/0'.format(REDIS_HOSTNAME),	
				backend='redis://{}:6379/0'.format(REDIS_HOSTNAME))

app.conf.update(
	CELERY_ACCEPT_CONTENT=['json'],
	CELERY_TASK_SERIALIZER='json',
	CELERY_RESULT_SERIALIZER='json',
)




##################################################################
##### THE TASKS ##################################################
##################################################################

@app.task
def chemaxon_task(request_post):
	logging.info("celery worker consuming cts chemaxon task..")
	try:
		_task_obj = CTSTasks()
		_results = JchemCalc().data_request_handler(request_post)
		_task_obj.redis_conn.publish(request_post.get('sessionid'), json.dumps(_results))
	except KeyError as ke:
		# TODO: Improve excpetion handling!!!
		logging.warning("exception in chemaxon_task: {}".format(ke))
		raise KeyError("Request to calc task needs 'calc' and 'service' keys")

@app.task
def epi_task(request_post):

	_task_obj = CTSTasks()
	_results = epi_calc.data_request_handler(request_post)
	_response_info = {}
	 # key:vals to add to response data objects:
	for key, val in _results.items():
		if not key == 'data':
			_response_info[key] = val

	for _data_obj in _results.get('data', []):
		_epi_prop = _data_obj.get('prop')
		_cts_prop_name = epi_calc.props[epi_calc.epi_props.index(_epi_prop)] # map epi ws key to cts prop key

		_method = None
		if _data_obj['prop'] == 'water_solubility':
			_method = _data_obj['method']

		if _cts_prop_name in props:
			_data_obj.update(_response_info)  # data obj going to client needs some extra keys
			_data_obj['prop'] = _cts_prop_name
			
			if _method:
				_data_obj['method'] = _method

			_task_obj.redis_conn.publish(request_post.get('sessionid'), json.dumps(_data_obj))


@app.task
def measured_task(request_post):
	logging.info("celery worker consuming cts measured task..")

	_task_obj = CTSTasks()
	measured_calc = MeasuredCalc()

	try:
		_results = measured_calc.data_request_handler(request_post)
		_results['calc'] == calc
		_returned_props = []  # keeping track of any missing prop data that was requested

		if 'error' in _results:
			for prop in props:
				_results.update({'prop': prop, 'data': _results.get('error')})
				_task_obj.redis_conn.publish(request_post.get('sessionid'), json.dumps(_results))
			return

		for _data_obj in _results.get('data'):
			for prop in props:
				# looping user-selected props (cts named props):
				if _data_obj['prop'] == measured_calc.propMap[prop]['result_key']:
					_results.update({'prop': prop, 'data': _data_obj.get('data')})
					_task_obj.redis_conn.publish(request_post.get('sessionid'), json.dumps(_results))
					_returned_props.append(prop)

		# Check for any missing prop data that user requested..
		_diff_set = set(_returned_props)^set(props)
		for missing_prop in _diff_set:
			logging.warning("{} missing from Measured response..".format(missing_prop))
			_results.update({'prop': missing_prop, 'data': "N/A"})
			_task_obj.redis_conn.publish(request_post.get('sessionid'), json.dumps(_results))  # push missing props up as "N/A"
	
	except Exception as e:
		logging.warning("Exception occurred in Measured task: {}".format(e))
		logging.warning("Sending request_post with 'error' as 'data' value..")
		_task_obj.redis_conn.publish(request_post.get('sessionid'), json.dumps(cts_task.build_error_obj(request_post, "error")))



@app.task
def test_task(request_post):
	logging.info("celery worker consuming cts test (calc) task..")
	try:
		_task_obj = CTSTasks()
		# _task_obj.initiate_requests_parsing(request_post)
		_results = TestCalc().data_request_handler(request_post)
		_task_obj.redis_conn.publish(request_post.get('sessionid'), json.dumps(_results))
	except KeyError as ke:
		# TODO: Improve excpetion handling!!!
		logging.warning("exception in chemaxon_task: {}".format(ke))
		raise KeyError("Request to calc task needs 'calc' and 'service' keys")

@app.task
def sparc_task(request_post):
	logging.info("celery worker consuming cts sparc task..")
	try:
		_task_obj = CTSTasks()
		# _task_obj.initiate_requests_parsing(request_post)
		_results = SparcCalc().data_request_handler(request_post)
		_task_obj.redis_conn.publish(request_post.get('sessionid'), json.dumps(_results))
	except KeyError as ke:
		# TODO: Improve excpetion handling!!!
		logging.warning("exception in chemaxon_task: {}".format(ke))
		raise KeyError("Request to calc task needs 'calc' and 'service' keys")

@app.task
def metabolizer_task(request_post):
	logging.info("celery worker consuming cts metabolizer task..")
	try:
		_task_obj = CTSTasks()
		# _task_obj.initiate_requests_parsing(request_post)
		_results = MetabolizerCalc().data_request_handler(request_post)
		_task_obj.redis_conn.publish(request_post.get('sessionid'), json.dumps(_results))
	except KeyError as ke:
		# TODO: Improve excpetion handling!!!
		logging.warning("exception in chemaxon_task: {}".format(ke))
		raise KeyError("Request to calc task needs 'calc' and 'service' keys")

@app.task
def cheminfo_task(request_post):
	logging.info("celery worker consuming cts cheminfo task..")
	try:
		_task_obj = CTSTasks()
		# _task_obj.initiate_requests_parsing(request_post)
		_results = ChemInfo().get_cheminfo(request_post)
		_task_obj.redis_conn.publish(request_post.get('sessionid'), json.dumps(_results))
	except KeyError as ke:
		# TODO: Improve excpetion handling!!!
		logging.warning("exception in cheminfo_task: {}".format(ke))
		raise KeyError("Request to calc task needs 'calc' and 'service' keys")

@app.task
def removeUserJobsFromQueue(sessionid):
	_task_obj = QEDTasks()
	logging.info("clearing celery task queues from user {}..".format(sessionid))
	_task_obj.revoke_queued_jobs(sessionid)  # clear jobs from celery
	logging.info("clearing redis cache from user {}..".format(sessionid))
	_task_obj.remove_redis_jobs(sessionid)  # clear jobs from redis


@app.task
def test_celery(sessionid, message):
	logging.info("!!!received message: {}".format(message))
	Calculator().redis_conn.publish(sessionid, "hello from celery")  # async push to user








##################################################################
########## App classes used by the celery tasks ##################
##################################################################

class QEDTasks(object):
	"""
	Suggested main class for task related things.
	Anything similar across all apps for task handling
	could go here.

	NOTE: Current setup requires redis host and port to instantiate
	"""
	def __init__(self):
		REDIS_HOSTNAME = os.environ.get('REDIS_HOSTNAME', 'localhost')
		REDIS_PORT = os.environ.get('REDIS_PORT', 6379)
		self.redis_conn = redis.StrictRedis(host=REDIS_HOSTNAME, port=REDIS_PORT, db=0)

	def remove_redis_jobs(self, sessionid):
		"""
		Removes the job IDs stored in redis after
		a user is finished with them
		"""
		try:
			user_jobs_json = self.redis_conn.get(sessionid)  # all user's jobs
			logging.info("user's jobs: {}".format(user_jobs_json))
			if user_jobs_json:
				self.redis_conn.delete(sessionid)  # remove key:vals from user
			return True
		except Exception as e:
			raise e

	def revoke_queued_jobs(self, sessionid):
		"""
		Revokes jobs yet started on the worker queues.
		Happens if user hits "cancel" or leaves page while
		requesting data, and is meant to prevent the queues 
		from clogging up with requests.
		"""
		user_jobs_json = self.redis_conn.get(sessionid)
		logging.info("{} JOBS: {}".format(sessionid, user_jobs_json))
		if not user_jobs_json:
			logging.info("no user jobs, moving on..")
			return
		user_jobs = json.loads(user_jobs_json)
		for job_id in user_jobs['jobs']:
			logging.info("revoking job {}".format(job_id))
			revoke(job_id, terminate=True)  # stop user job
			logging.info("revoked {} job".format(job_id))
		self.redis_conn.publish(sessionid, json.dumps({'status': "p-chem data request canceled"}))




class CTSTasks(QEDTasks):
	"""
	General class for cts tasks to call,
	and keeping tasks as single-level functions
	for now. Seems like the Task class has changed
	from celery 3 to 4 (http://docs.celeryproject.org/en/latest/whatsnew-4.0.html)
	"""
	def __init__(self):
		QEDTasks.__init__(self)

	def build_error_obj(self, request_post, error_message):
		default_error_obj = {
			'chemical': request_post['chemical'],
			'calc': request_post['calc'],
			'prop': request_post['prop'],
			'data': error_message
		}
		return default_error_obj


	# def initiate_requests_parsing(self, request_post):
	#     """
	#     Checks if request is single chemical or list of chemicals, then 
	#     parses request up to fill worker queues w/ single chemical requests.
	#     This was originally structured this way because revoking celery work
	#     seems to only be successful for jobs not yet started.

	#     It accounts for the case of a user requesting data for many chemicals
	#     (single job), then leaving page; the celery workers would continue processing
	#     that job despite the user not being there :(
	#     """
	#     logging.info("Request post coming into cts_task: {}".format(request_post))
	#     if 'nodes' in request_post:
	#         for node in request_post['nodes']:
	#             request_post['node'] = node
	#             request_post['chemical'] = node['smiles']
	#             request_post['mass'] = node['mass']
	#             jobID = self.parse_by_service(request_post.get('sessionid'), request_post)
	#     else:
	#         jobID = self.parse_by_service(request_post.get('sessionid'), request_post)


	# def parse_by_service(self, sessionid, request_post):
	#     """
	#     Further parsing of user request.
	#     Checks if 'service', if not it assumes p-chem request
	#     TODO: at 'pchem' service instead of assuming..

	#     Output: Returns nothing, pushes to redis (may not stay this way)
	#     """
	#     request_post['sessionid'] = sessionid

	#     if request_post.get('service') == 'getSpeciationData':
	#         logging.info("celery worker consuming chemaxon task")
	#         _results = JchemCalc().data_request_handler(request_post)
	#         self.redis_conn.publish(sessionid, json.dumps(_results))

	#     elif (request_post.get('service') == 'getTransProducts'):
	#         logging.info("celery worker consuming metabolizer task")
	#         _results = MetabolizerCalc().data_request_handler(request_post)
	#         self.redis_conn.publish(sessionid, json.dumps(_results))

	#     elif (request_post.get('service') == 'getChemInfo'):
	#         logging.info("celery worker consuming cheminfo task")
	#         # _results = getChemInfo(request_post)
	#         _results = ChemInfo().get_cheminfo(request_post)
	#         self.redis_conn.publish(sessionid, json.dumps(_results))
	#     else:
	#         self.parse_pchem_request(sessionid, request_post)

	#     return


	# def parse_pchem_request(self, sessionid, request_post):
	#     """
	#     This function loops a user's p-chem request and parses
	#     the work by calculator.

	#     Output: Returns nothing, pushes to redis (may not stay this way, instead
	#     the redis pushing may be handled at the task function level).
	#     """

	#     calc = request_post['calc']
	#     props = request_post['pchem_request'][calc]

	#     if calc == 'measured':
	#         measured_calc = MeasuredCalc()
	#         _results = measured_calc.data_request_handler(request_post)
	#         _results['calc'] == calc
	#         _returned_props = []  # keeping track of any missing prop data that was requested

	#         if 'error' in _results:
	#             for prop in props:
	#                 _results.update({'prop': prop, 'data': _results.get('error')})
	#                 self.redis_conn.publish(sessionid, json.dumps(_results))
	#             return

	#         for _data_obj in _results.get('data'):
	#             for prop in props:
	#                 # looping user-selected props (cts named props):
	#                 if _data_obj['prop'] == measured_calc.propMap[prop]['result_key']:
	#                     _results.update({'prop': prop, 'data': _data_obj.get('data')})
	#                     self.redis_conn.publish(sessionid, json.dumps(_results))
	#                     _returned_props.append(prop)

	#         # Check for any missing prop data that user requested..
	#         _diff_set = set(_returned_props)^set(props)
	#         for missing_prop in _diff_set:
	#             logging.warning("{} missing from Measured response..".format(missing_prop))
	#             _results.update({'prop': missing_prop, 'data': "N/A"})
	#             self.redis_conn.publish(sessionid, json.dumps(_results))  # push up as "N/A"

	#     elif calc == 'epi':

	#         epi_calc = EpiCalc()

	#         # Now that EPI returns all prop results in one request, the
	#         # melting point workflow must change. It'd probably be most
	#         # efficient to get melting point once, like at this level.
	#         # cts_rest.py in cts_api has a request object with 'prop' key, which
	#         # is how epi handled websocket/celery requests before the epi update.

	#         # For now, it'd be easiest to check for water_sol or vapor_press here,
	#         # and if either or both exist add a key with val of 'water_sol'. This
	#         # will trigger epi_calculator.py to use a 'melting_point' when making
	#         # a request to epiws...

	#         epi_props_list = request_post.get('pchem_request', {}).get('epi', [])

	#         if 'water_sol' in epi_props_list or 'vapor_press' in epi_props_list:
	#             request_post['prop'] = 'water_sol'  # trigger cts epi calc to get MP for epi request

	#         _results = epi_calc.data_request_handler(request_post)
	#         _response_info = {}

	#         # key:vals to add to response data objects:
	#         for key, val in _results.items():
	#             if not key == 'data':
	#                 _response_info[key] = val

	#         for _data_obj in _results.get('data', []):
	#             _epi_prop = _data_obj.get('prop')
	#             _cts_prop_name = epi_calc.props[epi_calc.epi_props.index(_epi_prop)] # map epi ws key to cts prop key

	#             _method = None
	#             if _data_obj['prop'] == 'water_solubility':
	#                 _method = _data_obj['method']

	#             if _cts_prop_name in props:
	#                 _data_obj.update(_response_info)  # data obj going to client needs some extra keys
	#                 _data_obj['prop'] = _cts_prop_name
					
	#                 if _method: _data_obj['method'] = _method

	#                 self.redis_conn.publish(sessionid, json.dumps(_data_obj))

	#     else:

	#         for prop_index in range(0, len(props)):

	#             prop = props[prop_index]
	#             request_post['prop'] = prop

	#             is_chemaxon = calc == 'chemaxon'
	#             is_kow = prop == 'kow_no_ph' or prop == 'kow_wph'
	#             if is_chemaxon and is_kow:

	#                 chemaxon_calc = JchemCalc()

	#                 for i in range(0, len(chemaxon_calc.methods)):
	#                     request_post['method'] = chemaxon_calc.methods[i]
	#                     _results = chemaxon_calc.data_request_handler(request_post)
	#                     self.redis_conn.publish(sessionid, json.dumps(_results))

	#             else:

	#                 if calc == 'chemaxon':
	#                     _results = JchemCalc().data_request_handler(request_post)
	#                     self.redis_conn.publish(sessionid, json.dumps(_results))

	#                 elif calc == 'sparc':
	#                     _results = SparcCalc().data_request_handler(request_post)
	#                     self.redis_conn.publish(sessionid, json.dumps(_results))

	#                 # elif calc == 'epi':
	#                 #     epi_calc = EpiCalc()
	#                 #     _results = epi_calc.data_request_handler(request_post)

	#                 #     logging.info("EPI RESULTS: {}".format(_results))
	#                 #     for _data_obj in _results.get('data', {}).get('data'):
	#                 #         logging.info("requested prop: {}".format(prop))
	#                 #         logging.info("epi props: {}".format(epi_calc.epi_props))
	#                 #         _epi_prop = _data_obj.get('prop')
	#                 #         _data_obj['prop'] = epi_calc.props[epi_calc.epi_props.index(_epi_prop)] # map epi ws key to cts prop key
	#                 #         _data_obj.update(request_post)  # add request key:vals to result
	#                 #         self.redis_conn.publish(sessionid, json.dumps(_data_obj))

	#                 elif calc == 'test':
	#                     _results = TestCalc().data_request_handler(request_post)
	#                     self.redis_conn.publish(sessionid, json.dumps(_results))