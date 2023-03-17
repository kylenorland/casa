#Head Material
#leftPorts=1
#rightPorts=1
#done

#------------------------File Documentation--------------------------
#Title: CirclingAndEscape
#Author: Kyle Norland
#Date: 6/18/19
#Description: Show how a PID controller leads to circling, and then fix it with
#               an extra term.



#-----------------------Imports and Set up---------------------------#
import pygame
from pygame.locals import *
import random #For randomly placing the enemies
import math

#Set up clock
clock = pygame.time.Clock()

#---------------------------Sideparts---------------------------------
class Sider(pygame.sprite.Sprite):
    def __init__(self):
        super(Sider, self).__init__()
        #Size
        self.surf = pygame.Surface((10,10))
        #Color
        self.surf.fill((100,100,100))
        #Start Location
        self.currentX = 350
        self.currentY = 250

        self.rect = self.surf.get_rect(center=(self.currentX, self.currentY))


#-------------------------Plane Class--------------------------------#
class Plane(pygame.sprite.Sprite):
    def __init__(self):
        super(Plane, self).__init__()
        #Size
        self.surf = pygame.Surface((30,20))
        #Color
        self.surf.fill((255,255,255))
        #Start Location
        self.currentX = 350
        self.currentY = 250

        self.rect = self.surf.get_rect(center=(self.currentX, self.currentY))

        #Stored original image
        self.storedImage = self.surf

        #STATS:
        self.turnRadius = 50
        self.angleSpeed = 3
        self.velocity = 5
        self.accelerationCap = 0.02
        self.orientation = 0
        self.tooClose = True

        #PID help
        self.errorSum = 0

    def update(self, pressed_keys):

        #---------------Angular Updating----------------
        #Define the PID terms and other settings
        pWeight = 1
        iWeight = 0
        dWeight = 0
        maxTurnAngle = 3

        #Determine whether the target point is within the reachable space of the plane
        self.turnRadius = (180 * self.velocity) / (maxTurnAngle * math.pi)
        #self.turnRadius = 95
        print("#########")
        print("The turn radius is: " + str(self.turnRadius))

        #Calculate the orientation to the objective
        deltaX = goal.currentX - self.currentX
        deltaY = -(goal.currentY - self.currentY) #Negative to flip the coordinate system)

        #Calculate desired orientation (It is relative to the forward x direction)
        angleToGoal = math.degrees(math.atan2(deltaY, deltaX))

        #Convert to 0-360 to be in absolute
        if angleToGoal < 0:
            angleToGoal = 360 + angleToGoal

        #Now, calculate the difference between the two angles
        error = angleToGoal - self.orientation
        error = (error + 180) % 360 - 180
        print("angleToGoal is: " + str(angleToGoal))
        print("Orientation is: " + str(self.orientation))
        print("Error is :" + str(error))


        #Position term
        pTerm = pWeight * error

        #Sum the terms
        total = pTerm
        #print("The total is: " + str(total))

        #------------------The added push out term---------------------------
        #Now, get the two angles
        leftAngle = self.orientation + 90
        rightAngle = self.orientation - 90
        if rightAngle < 0:
            rightAngle = 360 + rightAngle

        #Now, calculate a point in those directions
        leftPointX = self.currentX + (self.turnRadius * math.cos(math.radians(leftAngle)))
        leftPointY = self.currentY + (self.turnRadius * -(math.sin(math.radians(leftAngle)))) #To switch to the flipped y coordinates

        rightPointX = self.currentX + (self.turnRadius * math.cos(math.radians(rightAngle)))
        rightPointY = self.currentY + (self.turnRadius * -(math.sin(math.radians(rightAngle))))

        #Change the locations of the siders
        leftSider.currentX = leftPointX
        leftSider.currentY = leftPointY
        rightSider.currentX = rightPointX
        rightSider.currentY = rightPointY

        rightSider.rect = rightSider.surf.get_rect(center=(rightSider.currentX, rightSider.currentY))
        leftSider.rect = leftSider.surf.get_rect(center=(leftSider.currentX, leftSider.currentY))

        #print("The leftPoint is: " + str(leftPointX) + "====" + str(leftPointY))
        #print("The rightPoint is: " + str(rightPointX) +"====" + str(rightPointY))

        #Now, check the distance of the target point from both of these points
        leftDistance = math.sqrt(((leftPointX - goal.currentX)**2) + ((leftPointY - goal.currentY)**2))
        rightDistance = math.sqrt(((rightPointX - goal.currentX)**2) + ((rightPointY - goal.currentY)**2))

        #Print those to check
        #print("The left distance is: " + str(leftDistance))
        #print("The right distance is: " + str(rightDistance))

        print("The closer one is: " + str(min(leftDistance,rightDistance)))

        #Restrict to degree changes
        if abs(total) > abs(maxTurnAngle):
            actual = math.copysign(1,total) * maxTurnAngle #Negative because the actual right turn is in the clockwise direction
            print("hello")
        else:
            actual = total #Same reasoning as above

        #Momentum adder(like integral one, to overshoot, but then decline to zero)



        #Apply a push out force on the degree movement (To push it out so its reachable)
        inDistance = (self.turnRadius - (min(leftDistance,rightDistance)))
        pushOutForce = (1/10)*((inDistance + 10)**3)
        if inDistance < 0:
            pushOutForce = 0
        #((1/5)* inDistance) + math.copysign( #(1)*((1.03**(self.turnRadius - (min(leftDistance,rightDistance))))) - 2

        print("push out force is: " + str(pushOutForce))
        actual = actual + ((-1* math.copysign(1,total) * pushOutForce))
        print("Modified: " + str(actual))

        #Check again for outside of range
        total = actual

        #Restrict to degree changes
        if abs(total) > abs(maxTurnAngle):
            actual = (total/abs(total)) * maxTurnAngle #Negative because the actual right turn is in the clockwise direction
        else:
            actual = total #Same reasoning as above

        print("Actual is: " + str(actual))

        """
        #If too close, make to 2 instead
        if self.tooClose == True:
            actual = (1/3) * actual
            print("Too close")
            if min(leftDistance, rightDistance) > self.turnRadius:
                self.tooClose = False

        print("Actual is: " + str(actual))
        """
        #If good, then just do the


        #Finally, enact it
        self.orientation = self.orientation + actual

        #Correct for the 0 to 360 and 360 to higher edges
        if self.orientation > 360:
            self.orientation = self.orientation % 360
        elif self.orientation < 0:
            self.orientation = self.orientation + 360

        #print("The acted upon orientation is: " + str(self.orientation))

        #Move in that direction
        self.currentX = self.currentX + (self.velocity * math.cos(math.radians(self.orientation)))
        self.currentY = self.currentY - (self.velocity * math.sin(math.radians(self.orientation))) #Flip back to upside down coordinates for display

        #Approximate the exact
        approximateX = round(self.currentX)
        approximateY = round(self.currentY)

        #Move the plane to the approximate
        self.rect = self.surf.get_rect(center=(approximateX, approximateY))




        """
        #-----------------Calculate other forces and enace behavior---------------

        #Add air resistance to make a terminal velocity
        print("Acceleration is : " + str(actual))
        airResistance = -(self.velocity + actual) * (1/10)
        print("Air Resistance is: " + str(airResistance))

        #Add a "gravitational" force
        pullBack = -1

        self.velocity = self.velocity + actual + airResistance + pullBack
        #Print
        print("The velocity is : " + str(self.velocity))
        print(" ")

        #Update the exact plane location
        self.currentX = self.currentX + self.velocity

        #Approximate the exact
        approximateX = round(self.currentX)

        #Move the plane to the exact
        self.rect = self.surf.get_rect(center=(approximateX, self.currentY))
        """


        #Keep player on screen
        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > 800:
            self.rect.right = 800
        if self.rect.top <= 0:
            self.rect.top = 0
        elif self.rect.bottom >= 600:
            self.rect.bottom = 600




        #---------------Angular with Extra term---------


#----------------------Goal Class---------------------------
class Goal(pygame.sprite.Sprite):
    def __init__(self):
        super(Goal, self).__init__()
        self.surf = pygame.Surface((30,20))
        self.surf.fill((0,255,255))
        self.currentX = 400
        self.currentY = 300
        self.rect = self.surf.get_rect(center=(self.currentX,self.currentY))


#-------------------------Game Operation--------------------
#Initialize pygame
pygame.init()

#Create screen
screen = pygame.display.set_mode((800,600))

#Initialize Plane and Goal and Siders
plane = Plane()
goal = Goal()
leftSider = Sider()
rightSider = Sider()

#Take the original surface

#Initialize sprite groups
all_sprites = pygame.sprite.Group()
all_sprites.add(plane)
all_sprites.add(goal)
all_sprites.add(leftSider)
all_sprites.add(rightSider)

#Loop Variable
running = True

#Main Loop-----Exit Conditions and Sprite Updating
while running:
    #Event queue for loop
    for event in pygame.event.get():
        #Check for KEYDOWNs
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                running = False
        elif event.type == QUIT:
            running = False

    #Check the pressed keys to control
    pressed_keys = pygame.key.get_pressed()
    #Update player position
    plane.update(pressed_keys)


    ##SCREEN UPDATING
    #Clear Screen
    screen.fill((0,0,0))

    #Blit everything to screen
    for entity in all_sprites:
        screen.blit(entity.surf, entity.rect)

    #Draw circles around the left and right points
    pygame.draw.circle(screen, (255,255,255), (round(leftSider.currentX), round(leftSider.currentY)), round(plane.turnRadius), 1)
    pygame.draw.circle(screen, (255,255,255), (round(rightSider.currentX), round(rightSider.currentY)), round(plane.turnRadius), 1)

    #Check for collision
    if pygame.sprite.collide_rect(plane,goal):
        #plane.kill()
        print("Killed")

    #Update display
    pygame.display.flip()

    #Add delay to sync on all computers
    clock.tick(60)

#Close the display when everything is done
pygame.display.quit()
pygame.quit()



"""
        #---------------Linear Updating-----------------
        #Define the PID terms
        pWeight = 0.01
        iWeight = 0.0001
        dWeight = 0

        #Calculate error (x distance from goal)
        goalX = goal.currentX
        error = goal.currentX - self.currentX
        print("The error is: " + str(error))

        #---Position Term---
        pTerm = pWeight * error

        #---Integral Term---
        iTerm = iWeight * self.errorSum
        #Add to the sum
        self.errorSum = self.errorSum + error


        #Calculate Total
        total = pTerm + iTerm

        #Calculate Actual (Within Speed)
        print("The total is: " + str(total))
        actual = total
        #---------------End Linear Updating
"""
