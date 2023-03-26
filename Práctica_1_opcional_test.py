from multiprocessing import Process
from multiprocessing import BoundedSemaphore, Semaphore, Lock
from multiprocessing import current_process
from multiprocessing import Value, Array
import random

NPROD = 3
k = 10 #cada productor produce k-1 números y, por último, un -1


def productor(listaalmacenpriv, lista_empty, lista_non_empty, listaindexpriv, contador):

  valor = 0
  for i in range(k-1):
    dato = random.randint(0,5)
    valor+=dato
    print (f"productor {current_process().name} produciendo {valor}")
    lista_empty[int(current_process().name)].acquire()
    add_datapriv(valor, int(current_process().name), listaalmacenpriv, lista_empty, lista_non_empty, listaindexpriv) #el productor añade lo que ha producido a su almacén
    lista_non_empty[int(current_process().name)].release()
    print (f"productor {current_process().name} almacenando {valor}")
    
  lista_empty[int(current_process().name)].acquire()
  add_datapriv(-1, int(current_process().name), listaalmacenpriv, lista_empty, lista_non_empty, listaindexpriv)#añadimos el -1 al final
  lista_non_empty[int(current_process().name)].release()
  contador.value += 1
  
def add_datapriv(valor, pos, listaalmacenpriv, lista_empty, lista_non_empty, listaindexpriv): #el productor añade lo que ha producido a su almacén

  listaalmacenpriv[pos][listaindexpriv[pos].value] = valor
  listaindexpriv[pos].value += 1
  
			
def merge(almacencomun, listaalmacenpriv, lista_empty, lista_non_empty, index, listaindexaux, contador): #va a ser el que vaya añadiendo el mínimo, funciona como consumidor

  while contador.value < NPROD: #almacena hasta que haya todo -1, es decir, todos los productores han acabado de producir
    for i in range(NPROD):
      if listaalmacenpriv[i][listaindexaux[i].value] != -1:
        lista_non_empty[i].acquire() #espera a que todos los productores hayan producido algo y coge aquellos que no han acabado de producir
    
    minimo = get_minimo(listaalmacenpriv, lista_empty, lista_non_empty, listaindexaux, contador)
    add_minimo(minimo, almacencomun, lista_empty, lista_non_empty, index)
    lista_empty[minimo[1]].release() #despierta al productor del que ha cogido el mínimo
    for i in range(NPROD):
      if i != minimo[1]:
        lista_non_empty[i].release() 

  
def get_minimo(listaalmacenpriv, lista_empty, lista_non_empty, listaindexaux, contador): #nos va a dar una lista, el mínimo de almacenpriv y su posición

  minimo = [listaalmacenpriv[0][0], 0] #cogemos en principio como mínimo de referencia el primer elemento

  if contador.value == NPROD:
    minimo = [-1, -1] #esto en caso de que hayan acabado todos de producir y haya solo -1
    
  else: 
    for i in range(NPROD):
      if listaalmacenpriv[i][listaindexaux[i].value] >= 0:
        minimo = [listaalmacenpriv[i][listaindexaux[i].value], i] #aquí nos aseguramos de coger como referencia un número no negativo
    for i in range(NPROD):
      if listaalmacenpriv[i][listaindexaux[i].value] <= minimo[0] and listaalmacenpriv[i][listaindexaux[i].value] >= 0: #buscamos el mínimo (no negativo) comparando con el de referencia
        minimo = [listaalmacenpriv[i][listaindexaux[i].value], i]
    listaindexaux[minimo[1]].value += 1
        
  return minimo
    
        
def add_minimo(minimo, almacencomun, lista_empty, lista_non_empty, index): #añade el mínimo al almacencomun

  if minimo[0] >= 0:
    almacencomun[index.value] = minimo[0]
    index.value += 1
    print (f"consumidor consumiendo {minimo[0]} del productor {minimo[1]}")
    
    
def main():

  lista_empty = []
  lista_non_empty = []
  almacencomun =  Array('i', NPROD*(k-1)) #buffer donde almacena el consumidor los mínimos
  index = Value('i', 0) #índice de la posición en el almacencomun
  contador = Value('i', 0) #cuenta los -1, es decir, cuántos productores han acabado de producir
  
  listaalmacenpriv = [] #lista de los almacenes de cada productor
  listaindexpriv = [] #lista de índices en cada almacén de cada productor
  listaindexaux = [] #lista de índices que dicen por dónde vamos cogiendo de cada almacén de cada productor
   
  for i in range(NPROD):
    empty = BoundedSemaphore(1) #semáforo de cada productor que controla que el productor produce un número
    non_empty = Semaphore(0) #semáforo de cada productor que controla si ha acabado de producir un número
    lista_empty.append(empty)
    lista_non_empty.append(non_empty)
    
    almacenaux = Array ('i', k)
    listaalmacenpriv.append(almacenaux)
    indexpriv = Value('i', 0)
    listaindexpriv.append(indexpriv)
    indexaux = Value('i', 0)
    listaindexaux.append(indexaux)
        
  productores = [Process(target = productor, name=f'{i}', args = (listaalmacenpriv, lista_empty, lista_non_empty, listaindexpriv, contador)) for i in range(NPROD)]
  consumidor = Process(target = merge, args = (almacencomun, listaalmacenpriv, lista_empty, lista_non_empty, index, listaindexaux, contador))
        
  for p in productores:
    p.start()  
  consumidor.start()
  
  for p in productores:
    p.join()     
  consumidor.join()
  
  print(almacencomun[:])
  
if __name__ == '__main__':
  main()
