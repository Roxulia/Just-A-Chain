from PIL import Image

# Open the .jpg image
img = Image.open('jac.png')

# Save it as .ico (you can specify sizes, like 64x64, or let it use the default)
img.save('jac.ico', format='ICO', sizes=[(64, 64)])
