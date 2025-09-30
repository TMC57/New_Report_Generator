import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math

class GameObject:
    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z
        self.rotation_x = 0
        self.rotation_y = 0
        self.rotation_z = 0

    def update(self):
        pass

    def render(self):
        pass

class Cube(GameObject):
    def __init__(self, x=0, y=0, z=0, size=1):
        super().__init__(x, y, z)
        self.size = size
        self.vertices = [
            [1, -1, -1], [1, 1, -1], [-1, 1, -1], [-1, -1, -1],
            [1, -1, 1], [1, 1, 1], [-1, -1, 1], [-1, 1, 1]
        ]
        self.edges = [
            [0,1], [1,2], [2,3], [3,0],
            [4,5], [5,7], [7,6], [6,4],
            [0,4], [1,5], [2,7], [3,6]
        ]

    def update(self):
        self.rotation_y += 1
        self.rotation_x += 0.5

    def render(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.rotation_x, 1, 0, 0)
        glRotatef(self.rotation_y, 0, 1, 0)
        glScalef(self.size, self.size, self.size)

        glColor3f(0, 1, 0)  # Vert
        glBegin(GL_LINES)
        for edge in self.edges:
            for vertex in edge:
                glVertex3fv(self.vertices[vertex])
        glEnd()

        glPopMatrix()

class Pyramid(GameObject):
    def __init__(self, x=0, y=0, z=0, size=1):
        super().__init__(x, y, z)
        self.size = size
        self.vertices = [
            [0, 1, 0],     # Sommet
            [1, -1, 1],    # Base
            [-1, -1, 1],
            [-1, -1, -1],
            [1, -1, -1]
        ]
        self.edges = [
            [0,1], [0,2], [0,3], [0,4],  # Du sommet vers la base
            [1,2], [2,3], [3,4], [4,1]   # Base
        ]

    def update(self):
        self.rotation_y += 2

    def render(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.rotation_y, 0, 1, 0)
        glScalef(self.size, self.size, self.size)

        glColor3f(1, 0, 0)  # Rouge
        glBegin(GL_LINES)
        for edge in self.edges:
            for vertex in edge:
                glVertex3fv(self.vertices[vertex])
        glEnd()

        glPopMatrix()

class Sphere(GameObject):
    def __init__(self, x=0, y=0, z=0, radius=1):
        super().__init__(x, y, z)
        self.radius = radius

    def update(self):
        self.rotation_z += 1.5

    def render(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.rotation_z, 0, 0, 1)

        glColor3f(0, 0, 1)  # Bleu

        # Dessiner des cercles pour simuler une sphère
        segments = 20
        for i in range(3):
            glBegin(GL_LINE_LOOP)
            for j in range(segments):
                angle = 2 * math.pi * j / segments
                if i == 0:  # Cercle XY
                    glVertex3f(self.radius * math.cos(angle), self.radius * math.sin(angle), 0)
                elif i == 1:  # Cercle XZ
                    glVertex3f(self.radius * math.cos(angle), 0, self.radius * math.sin(angle))
                else:  # Cercle YZ
                    glVertex3f(0, self.radius * math.cos(angle), self.radius * math.sin(angle))
            glEnd()

        glPopMatrix()

class Game3D:
    def __init__(self):
        pygame.init()
        self.width, self.height = 800, 600
        self.screen = pygame.display.set_mode((self.width, self.height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Jeu 3D - Apprentissage OOP")

        # Configuration OpenGL
        glEnable(GL_DEPTH_TEST)
        gluPerspective(45, (self.width/self.height), 0.1, 50.0)
        glTranslatef(0.0, 0.0, -10)

        # Créer les objets du jeu
        self.objects = [
            Cube(-3, 0, 0, 1.5),
            Pyramid(0, 0, 0, 1.2),
            Sphere(3, 0, 0, 1.0)
        ]

        self.running = True
        self.clock = pygame.time.Clock()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

    def update(self):
        for obj in self.objects:
            obj.update()

    def render(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        for obj in self.objects:
            obj.render()

        pygame.display.flip()

    def run(self):
        print("Jeu 3D démarré !")
        print("Appuyez sur Échap pour quitter")

        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(60)

        pygame.quit()

if __name__ == "__main__":
    game = Game3D()
    game.run()