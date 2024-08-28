from BFA_Mongo_ELK import mongoDB_ELK
from Hashmap import Hashmap

''' This is the main function '''

if __name__ == '__main__':
	me = mongoDB_ELK()
	tls_elk=me.establish_connection_eck()
	fetch_data = me.fetch_db_data(tls_elk)
