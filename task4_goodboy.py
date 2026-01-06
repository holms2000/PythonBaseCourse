number_of_input_data_sets=int(input())
for i in range(number_of_input_data_sets):
 number_of_digits=int(input())
 num_list = input().split()
 l = [int(num_list[i]) for i in range(len(num_list)) if i < number_of_digits]
 mn=min(l)
 l.remove(mn)
 s=1
 for j in l:
     s*=j
 print(s*(mn+1))