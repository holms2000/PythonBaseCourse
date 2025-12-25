"""file task two"""
import math
def input_info():
    '''
    @requires: None
    @modifies: None
    @effects: None
    @raises: None
    @returns: receiving data from the input console
    '''
    d1 = int(input('Введите кратчайшее расстояние от спасателя до кромки воды, d1 (ярды) => '))
    d2 = int(input('Введите кратчайшее расстояние от утопающего до берега, d2 (футы) => '))
    h = int(input('Введите боковое смещение между спасателем и утопающим, h (ярды) => '))
    v_sand = int(input('Введите скорость движения спасателя по песку, v_sand (мили в час) => '))
    n = int(input('Введите коэффициент замедления спасателя при движении в воде, n => '))
    theta1 = float(input('Введите направление движения спасателя по песку, theta1 (градусы) => '))
    return d1,d2,h,v_sand,n,theta1

def find_x(d1,theta1):
    ''''
    @requires: d1 ϵ[1,1000]; theta1 ϵ[1.000,180.000]
    @modifies: None
    @effects: None
    @raises: None
    @returns: find x
    '''
    theta1=math.radians(theta1)
    x = d1*math.tan(theta1)
    return x

def find_L1(x,d1):
    ''''
    @requires: x, d1 ϵ[1,1000]
    @modifies: None
    @effects: None
    @raises: None
    @returns: find L1
    '''
    L1 = math.sqrt((x**2)+(d1**2))
    return L1

def find_L2(h,x,d2):
    ''''
    @requires: h, x, d2 ϵ[1,1000]
    @modifies: None
    @effects: None
    @raises: None
    @returns: find L2
    '''
    L2 = math.sqrt(((h - x)**2) + (d2**2))
    return L2

def find_t(L1,n,L2,v_sand):
    ''''
    @requires: L1, n, L2, v_sand ϵ[1,1000]
    @modifies: None
    @effects: None
    @raises: None
    @returns: find t
    '''
    t = (L1+(n*L2))/v_sand
    return t

def func_find(d1,d2,h,v_sand,n,theta1): 
    '''
    @requires: d1, d2, h, v_sand, n b ϵ[1,1000]; theta1 ϵ[1.000,180.000]
    @modifies: None
    @effects: None
    @raises: None
    @returns: the number of seconds it takes for a rescuer to reach a drowning person
    '''
    #в одном ярде 3 фута
    d1=d1*3
    #в одном ярде 3 фута
    h=h*3
    #в одной миле 5280 футов - 1 час это 60 * 60 секунд
    v_sand = v_sand*5280/(60**2)

    x = find_x(d1,theta1)
    
    L1 = find_L1(x,d1)
    
    L2 = find_L2(h,x,d2) 
    
    t = find_t(L1,n,L2,v_sand) 
    
    return t

def output_info(theta1,t):
    '''
    @requires: t ϵ[1,1000]; theta1 ϵ[1.000,180.000]
    @modifies: None
    @effects: None
    @raises: None
    @returns: displays the values ​​of variables in the console
    '''
    print(f'Если спасатель начнет движение под углом theta1, равным {theta1:.1f} градусам, он достигнет утопающего через {t:.1f} секунды')

#d1,d2,h,v_sand,n,theta1 = input_info()
#t = func_find(d1,d2,h,v_sand,n,theta1)
#output_info(theta1,t)

def test_time_save():
    '''
    @requires: None
    @modifies: None
    @effects: None
    @raises: None
    @returns: test def func_find
    '''
    total = 4
    passed = 0
    inputs =((8,10,50,5,2,25.413),(8,10,50,5,2,55.413),(8,10,50,5,2,77.413),(8,10,50,5,2,39.413)) 
    expected = (41.5,37.29,26.92,39.9)
    epsilon = 1.0e-1
    for i in range(len(inputs)):
        inp=inputs[i]
        t = func_find(inp[0],inp[1],inp[2],inp[3],inp[4],inp[5])
        print(t)
        if abs(t - expected[i]) > epsilon:
            print('Test failed')
        else:
            print('Test passed')
            passed +=1
            #output_info(inp[5],t)
    return total,passed

def test_x_L1_L2():
    '''
    @requires: None
    @modifies: None
    @effects: None
    @raises: None
    @returns: test functions find_x, find_L1, find_L2
    '''
    
    #в одном ярде 3 фута
    d1=8*3
    
    d2 = 10
    #в одном ярде 3 фута
    h = 50*3
    #в одной миле 5280 футов - 1 час это 60 * 60 секунд
    
    v_sand = 5*5280/(60**2)
    n =2 
    theta1 = 39.413

    x = find_x(d1,theta1)
    expected = 19.72
    epsilon = 1.0e-1
    if abs(x - expected) > epsilon:
        print('Test failed x')
    else:
        print('Test passed x')
    expected = 31.06
    L1 = find_L1(x,d1)
    if abs(L1 - expected) > epsilon:
        print('Test failed L1')
    else:
        print('Test passed L1')
    L2 = find_L2(h,x,d2) 
    expected = 130.66
    epsilon = 1.0e-1
    if abs(L2 - expected) > epsilon:
        print('Test failed L2')
    else:
        print('Test passed L2')
    expected = 31.06

    print(find_t(L1,n,L2,v_sand))

#total,passed=test_time_save()
#print(f'Total {total} tests run and {passed} of them passed.')

#test_x_L1_L2()

def float_range(start, stop, step):
    '''
    @requires: start,stop,step ϵ [0,180.001] 
    @modifies: None
    @effects: None
    @raises: None
    @returns: return float_range(start, stop, step)

    '''
    while start < stop:
        yield start
        start += step

def min_time_save():
    '''
    @requires: None
    @modifies: None
    @effects: None
    @raises: None
    @returns:  min time and angle value
    '''
    inputs =(8,10,50,5,2)
    mintime =100
    theta1 = 180
    for i in float_range(0, 180.001, 0.001):
        t = func_find(inputs[0],inputs[1],inputs[2],inputs[3],inputs[4],i)
        if t < mintime:
            mintime = t
            theta1 = i 
    return theta1,mintime 

theta1,mintime = min_time_save()

print(f'Быстрее всего спасатель доберется до утопающего при угле {theta1:.1f} за время {mintime:.1f} секунды.')