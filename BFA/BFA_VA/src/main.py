from vaCauses import vaCauses
from Hashmap import Hashmap
if __name__ == '__main__':
	va = vaCauses()
	es = va.establish_connection()
	tls_elk=va.establish_connection_eck()
	fetch_data = va.fetch_va_causes(es,tls_elk)
