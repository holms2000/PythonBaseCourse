def can_partition_array(n, array):
    total_sum = sum(array)
    if total_sum == 0:
        if array.count(0)!= n:
            return True
        else:
         return False   
    else:
        return True
 
def partition_array(n, array):
    result = []
    i = -1
    while (i <n) and i+1 < n:
      i+=1   
      if array[i]!= 0:
          for k in range(i,n):
              if array[k]!=0:
                  for j in range(k+1,n):
                      if array[j]!=0:
                          break
                      else:
                          k+=1
                  result.append((i+1, k+1))
                  i = k
                  break
      else:
          if i == 0:
              for k in range(i,n):
                  if array[k]!=0:
                      for j in range(k+1,n):
                          if array[j]!=0:
                              break
                          else:
                              k+=1
                      result.append((i+1, k+1))
                      i = k
                      break
    return result
 
def main_body(n,array):
        if not can_partition_array(n, array):
            print("NO")
        else:
            partitions = partition_array(n, array)
            
            print("YES")
            print(len(partitions))
            for p in partitions:
                print(p[0], p[1])

n =int(input())
ar=input().split()
array = [int(ar[i]) for i in range(n)]
main_body(n,array)
