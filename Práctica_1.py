from multiprocessing import Process
from multiprocessing import BoundedSemaphore, Semaphore, Lock
from multiprocessing import current_process
from multiprocessing import Value, Array
import random

NPROD = 3
k = 10

#sin la parte opcional


def productor(almacenpriv, lista_empty, lista_non_empty, contador, notoques):

  valor = 0
  for i in range(k):
    dato = random.randint(0,5)
    valor+=dato
    print (f"productor {current_process().name} produciendo {valor}")
    lista_empty[int(current_process().name)].acquire()
    add_data(valor, int(current_process().name), almacenpriv, lista_empty, lista_non_empty, notoques)
    lista_non_empty[int(current_process().name)].release()
    print (f"productor {current_process().name} almacenando {valor}")
    
  lista_empty[int(current_process().name)].acquire()
  add_data(-1, int(current_process().name), almacenpriv, lista_empty, lista_non_empty, notoques) #añadimos el -1 al final
  lista_non_empty[int(current_process().name)].release()
  contador.value += 1

			
def merge(almacenpriv, almacencomun, lista_empty, lista_non_empty, index, contador, notoques): #va a ser el que vaya añadiendo el mínimo, funciona como consumidor

  while contador.value < len(almacenpriv): #almacena hasta que haya todo -1, es decir, todos los productores han acabado de producir
    for i in range(NPROD):
      if almacenpriv[i] != -1:
        lista_non_empty[i].acquire() #espera a que todos los productores hayan producido algo y coge aquellos que no han acabado de producir
    
    minimo = get_minimo(almacenpriv, lista_empty, lista_non_empty, contador, notoques)
    add_minimo(minimo, almacenpriv, almacencomun, lista_empty, lista_non_empty, index, contador)
    lista_empty[minimo[1]].release() #despierta al productor del que ha cogido el mínimo
    for i in range(NPROD):
      if i != minimo[1]:
        lista_non_empty[i].release() 

                 
def add_data(valor, pos, almacenpriv, lista_empty, lista_non_empty, notoques): #el productor añade lo que ha producido

  notoques.acquire()
  almacenpriv[pos] = valor
  notoques.release()

def get_minimo(almacenpriv, lista_empty, lista_non_empty, contador, notoques): #nos va a dar una lista, el mínimo de almacenpriv y su posición

  notoques.acquire()
  tam = len(almacenpriv)
  minimo = [almacenpriv[0],0] #cogemos en principio como mínimo de referencia el primer elemento

  if contador.value == tam:
    minimo = [-1, -1] #esto en caso de que hayan acabado todos de producir y haya solo -1
    
  else: 
    for i in range(tam):
      if almacenpriv[i] >= 0:
        minimo = [almacenpriv[i], i] #aquí nos aseguramos de coger como referencia un número no negativo
    for i in range(tam):
      if almacenpriv[i] <= minimo[0] and almacenpriv[i] >= 0: #buscamos el mínimo (no negativo) comparando con el de referencia
        minimo = [almacenpriv[i], i]
  notoques.release()
        
  return minimo
    
        
def add_minimo(minimo, almacenpriv, almacencomun, lista_empty, lista_non_empty, index, contador): #añade el mínimo al almacencomun

  if minimo[0] >= 0:
    almacencomun[index.value] = minimo[0]
    index.value += 1
    print (f"consumidor consumiendo {minimo[0]} del productor {minimo[1]}")


def main():

  lista_empty = []
  lista_non_empty = []
  notoques = Lock() #va a controlar quién toca el almacenpriv
  almacenpriv = Array('i', NPROD) #buffer donde almacenan los productores y de donde coge el mínimo el consumidor
  almacencomun =  Array('i', NPROD*k) #buffer donde almacena el consumidor los mínimos
  index = Value('i', 0) #índice de la posición en el almacencomun
  contador = Value('i', 0) #cuenta los -1 del almacenpriv, es decir, cuántos productores han acabado de producir
  
  for i in range(NPROD):
    empty = BoundedSemaphore(1) #semáforo de cada productor que controla que el productor produce un número
    non_empty = Semaphore(0) #semáforo de cada productor que controla si ha acabado de producir un número
    lista_empty.append(empty)
    lista_non_empty.append(non_empty)
    
  productores = [Process(target = productor, name=f'{i}', args = (almacenpriv, lista_empty, lista_non_empty, contador, notoques)) for i in range(NPROD)]
  consumidor = Process(target = merge, args = (almacenpriv, almacencomun, lista_empty, lista_non_empty, index, contador, notoques))
  
  for i in range(NPROD):
    almacenpriv[i] = -2  #el almacén está vacío al inicio para todos los productores
        
  for p in productores:
    p.start()  
  consumidor.start()
  
  for p in productores:
    p.join()     
  consumidor.join()
  
  print(almacencomun[:])
  
if __name__ == '__main__':
  main()
