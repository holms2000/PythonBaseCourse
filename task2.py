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

    thetar=math.radians(theta1)
    
    x = d1*math.tan(thetar)
    
    L1 = math.sqrt((x**2)+(d1**2))
    
    L2 = math.sqrt(((h - x)**2) + (d2**2))
    
    t = (L1+(n*L2))/v_sand
    
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
    return total,passed

total,passed=test_time_save()
print(f'Total {total} tests run and {passed} of them passed.')

