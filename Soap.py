from xml.dom import minidom
import urllib2

html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
    }

def html_escape(text):
    """Produce entities within text."""
    L=[]
    for c in text:
        L.append(html_escape_table.get(c,c))
    return "".join(L)

class Soap(object):
	# 'private' methods
	def __init__(self, namespace, url, parser=None, debug=False):
		self.namespace = namespace
		self.url = url
		self.parser = parser
		self.debug_soap_requests = debug
		self.debug_soap_responses = debug

	def call(self, method, params):
		soap_params = self.xmlise_dict(params)
		print soap_params
		variables = {
			"method" : method,
			"namespace" : self.namespace,
			"params" : soap_params
		}
		
		env = '''<?xml version="1.0" encoding="utf-8"?>
		<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
			<soap:Body>
				<%(method)s xmlns="%(namespace)s">
					%(params)s
				</%(method)s>
			</soap:Body>
		</soap:Envelope>''' % variables
		
		soap_action = self.namespace+method
		
		if self.debug_soap_requests:
			print "Request %s (SOAPAction: %s):" % (self.url, soap_action)
			print env
		
		req = urllib2.Request(self.url, env)
		req.add_header('Content-Type', 'text/xml')
		req.add_header('SOAPAction', soap_action)
		try:
			hndl = urllib2.urlopen(req)
		except urllib2.HTTPError, ex:
			if self.debug_soap_responses:
				print "ERROR:"
				print ex
			raise ex
		
		resp = hndl.read()
		if self.debug_soap_responses:
			print "Response:"
			print resp
		
		
		if self.parser: return self.parser(method, resp)
		
		doc = minidom.parseString(resp)
		if doc.hasChildNodes():
			result_nodes = doc.getElementsByTagName(method+"Result")
			if len(result_nodes) == 1:
				node = result_nodes[0].firstChild
				return self.parse_recurse(node)
		
		return None


	def xmlise_dict(self, items):
		'''
		Supporting method for _soap_api_call.  Converts the dictionary into an XML string to be inserted into the SOAP envelope.
		
		Keyword arguments:
		- items: dictionary of items to convert to XML.
		'''
		if items == None or len(items) == 0:
			return ""
		
		if type(items) != dict:
			raise Exception("This method only supports dictionary types")
		
		resp = ""
		tmpl = "<%(k)s>%(v)s</%(k)s>\n"
		for k, v in items.items():
			ty = type(v) 
			if (ty == dict):
				resp += tmpl % { "k":k, "v": self.xmlise_dict(v) }
			elif (ty == list):
				resp+= "<%(k)s>\n" % {"k":k}
				for i in v:
					resp += self.xmlise_dict(i)
				resp+= "</%(k)s>\n" % {"k":k}
			else:
				resp += tmpl % { "k":k, "v": html_escape(str(v)) }
		
		return resp
	
	def parse_recurse(self, node, obj={}):
		if not node.hasChildNodes():
			return node.nodeValue
		
		for n in node.childNodes:
			obj[n.nodeName] = self.parse_recurse(n.firstChild)
		
		return obj
		
class SoapObject(Soap):
	extra_keys = {}
	def __init__(self, namespace, url, parse, debug, **kwargs):
		for key in kwargs:
			self.extra_keys[key] = kwargs[key]
		Soap.__init__(self, namespace, url, parse, debug)
		
	def call(self, method, params={}):
		if len(self.extra_keys): params = self.append_extra_keys(params)
		return Soap.call(self, method, params)
	
	def append_extra_keys(self, data):
		for key in self.extra_keys:
			data[key] = self.extra_keys[key]
		
		return data
	
	def _parse_args(self, args):
		props = {}
		for key in args:
			if type(args[key]).__name__ == 'dict': props[key] = self._parse_args(args[key])
			else: props[key] = args[key]
		
		return props
	
	def __getattr__(self, attr):
		def defmeth(**args):
			props = self._parse_args(args)
			print props
			cls = self.__class__.__name__
			return self.call(str(cls)+"."+attr, props)
		return defmeth