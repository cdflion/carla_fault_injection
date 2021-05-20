import glob
import os
import sys

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla
import fault_injector

import random
import time

def drawStrip(image):
    start_index = image.height*0.45*image.width
    end_index = image.height*0.55*image.width
    for i in range(int(start_index), int(end_index)):
        image.raw_data[4*i] = 255
        image.raw_data[4*i+1] = 255
        image.raw_data[4*i+2] = 255  
    return image

def drawCircle(image):
    if(image.height < image.width):
        radix = int(image.height/5)
    else:
        radix = int(image.width/5)
    for i in range(int(image.height/2 - radix), int(image.height/2 + radix)):
        for j in range(int(image.width/2 - radix), int(image.width/2 + radix)):
            if((i-image.height/2)**2 + (j-image.width/2)**2 < radix**2):
                image.raw_data[4*(i*image.width + j)] = 255
                image.raw_data[4*(i*image.width + j)+1] = 255
                image.raw_data[4*(i*image.width + j)+2] = 255  
    return image

def main():
    actor_list = []
    ccld = carla.ColorConverter.LogarithmicDepth
    ccr = carla.ColorConverter.Raw
    ccd = carla.ColorConverter.Depth
    try:
        client = carla.Client('localhost', 2000)
        client.set_timeout(200.0)
        world = client.get_world()
        blueprint_library = world.get_blueprint_library()
        bp = blueprint_library.filter('vehicle')[0]
        if bp.has_attribute('color'):
            color = bp.get_attribute('color').recommended_values[0]
            bp.set_attribute('color', color)
        transform = world.get_map().get_spawn_points()[0]
        vehicle = world.spawn_actor(bp, transform)
        actor_list.append(vehicle)
        
        camera_bp = blueprint_library.find('sensor.camera.depth')
        camera_transform = carla.Transform(carla.Location(x=1.5, z=2.4))
        camera_transform2 = carla.Transform(carla.Location(x=1.5, y=1.0, z=2.4))
        camera_transform3 = carla.Transform(carla.Location(x=1.5, y=2.0, z=2.4))
        camera_transform4 = carla.Transform(carla.Location(x=1.5, y=3.0, z=2.4))
        
        camera1 = world.spawn_actor(camera_bp, camera_transform, attach_to=vehicle)
        camera1 = fault_injector.ToFaultySensor(camera1)
        actor_list.append(camera1)
        defaultCB1 = lambda image: image.save_to_disk('always/%06d.png' % image.frame, ccr)
        faultCB1 = lambda image: drawCircle(image)
        camera1.listen(defaultCB1, faultCB1)
        
        camera2 = world.spawn_actor(camera_bp, camera_transform2, attach_to=vehicle)
        camera2 = fault_injector.ToFaultySensor(camera2)
        camera2.strategy = fault_injector.Strategy.INTERMITTENT
        camera2.target = 5
        actor_list.append(camera2)
        defaultCB2 = lambda image: image.save_to_disk('intermittent/%06d.png' % image.frame, ccd)
        faultCB2 = lambda image: drawCircle(image)
        camera2.listen(defaultCB2, faultCB2)
        
        camera3 = world.spawn_actor(camera_bp, camera_transform3, attach_to=vehicle)
        camera3 = fault_injector.ToFaultySensor(camera3)
        camera3.strategy = fault_injector.Strategy.TRANSIENT
        camera3.target = 5
        actor_list.append(camera3)
        defaultCB3 = lambda image: image.save_to_disk('transient/%06d.png' % image.frame, ccld)
        faultCB3 = lambda image: drawCircle(image)
        camera3.listen(defaultCB3, faultCB3)
        
        camera4 = world.spawn_actor(camera_bp, camera_transform4, attach_to=vehicle)
        camera4 = fault_injector.ToFaultySensor(camera4)
        camera4.strategy = fault_injector.Strategy.CRASH
        camera4.target = 7
        actor_list.append(camera4)
        defaultCB4 = lambda image: image.save_to_disk('crash/%06d.png' % image.frame, ccr)
        faultCB4 = lambda image: drawCircle(image)
        camera4.listen(defaultCB4, faultCB4)
        
        
        time.sleep(5)
        input("Press Enter to continue...")
    finally:
        print('destroying actors')
        camera1.destroy()
        camera2.destroy()
        camera3.destroy()
        camera4.destroy()
        client.apply_batch([carla.command.DestroyActor(x) for x in actor_list])
        print('done.')
if __name__ == '__main__':

    main()