# -*- coding: utf-8 -*-
# @Author: Matt Pedler
# @Date:   2017-07-14 12:42:48
# @Last Modified by:   Matt Pedler
# @Last Modified time: 2017-10-27 13:18:42
import re

def output_gib(in_name, out_name):
    Lorem_Ipsum = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Fusce ullamcorper sapien magna. Nulla libero dui, maximus ac hendrerit vel, pharetra ac ex. Cras vestibulum accumsan augue at venenatis. Aliquam quis vestibulum elit, et tristique erat. Pellentesque tincidunt augue euismod, lacinia neque non, pharetra risus. In vel tortor eget risus vehicula commodo non eu tortor. Duis quis ligula quis felis sagittis auctor id ac est. Aliquam placerat, nunc sit amet pretium convallis, sem est bibendum ligula, eget tincidunt erat metus quis quam. Aenean eget nisl consequat, cursus erat ac, laoreet purus. Praesent auctor sapien ante, nec ullamcorper ipsum egestas ut. Donec non convallis eros. Donec a dolor quis ligula porttitor finibus. Donec augue turpis, placerat vel magna sit amet, tempor tincidunt risus. Nullam felis tortor, rhoncus nec mauris sed, tincidunt scelerisque enim.Nullam aliquet mi arcu, quis fermentum purus pharetra quis. Nulla a posuere sapien. In hac habitasse platea dictumst. Maecenas molestie dignissim enim, vel efficitur nisi ultricies consequat. Etiam vulputate rutrum mi pharetra sagittis. Curabitur maximus erat a erat semper elementum. Suspendisse ut nulla lorem. Praesent tempor hendrerit metus, eu varius velit faucibus ut.Maecenas a massa et lorem tempus sollicitudin. Aliquam ac sapien vel sem congue ornare id nec eros. Duis tempor mattis purus, non malesuada neque posuere nec. Sed sem ipsum, pretium a pellentesque ac, pretium ac tortor. Vivamus cursus odio quis lorem aliquam, quis ultricies lacus molestie. Quisque quis ligula mauris. Phasellus et placerat justo, mattis viverra elit. Duis rhoncus, libero blandit feugiat rhoncus, nisl metus convallis nibh, vel bibendum odio quam ut nisi. Cras non lorem libero. Quisque quis purus quis orci ornare ullamcorper. Aliquam eu finibus ante. Pellentesque vitae hendrerit risus. Fusce odio elit, faucibus in velit at, pharetra ultricies metus. Mauris luctus accumsan varius. Quisque vitae lacinia lacus, sed interdum justo.Sed in ultricies ex, sed facilisis dui. Nulla finibus mauris vitae risus sagittis semper. Proin tellus dolor, rutrum a lacus vitae, congue lobortis eros. Quisque quam ex, porta a odio sit amet, blandit sodales eros. Curabitur magna purus, malesuada vitae venenatis nec, vehicula quis magna. Integer suscipit placerat tortor, sed blandit arcu molestie eu. Curabitur pretium vestibulum ante, et ultrices mauris pharetra eget. Sed vestibulum dui nec sapien faucibus, in ullamcorper odio interdum. Suspendisse a augue vestibulum, posuere sapien at, elementum sem. Cras tortor nisl, sagittis quis sapien a, elementum semper dolor. Proin varius mollis magna, sit amet posuere nunc tempor ac. Praesent viverra scelerisque nibh id vulputate. Sed tristique ex sit amet diam interdum scelerisque. Aenean nec ligula eget nulla ultricies tincidunt."
    Lorem_Copy = Lorem_Ipsum
    with open(in_name, "r") as original:
        with open(out_name, "w") as new:
            for line in original:
                if line.find("\"") != -1:

                    #Find first and last quotation
                    pos1 = line.find("\"")+1
                    pos2 = line.rfind("\"")

                    #rewrite the next line with random stuff
                    length = len(line[pos1:pos2])
                    if len(Lorem_Copy) < length:
                        Lorem_Copy = Lorem_Ipsum

                    new_line = line[0:pos1] + Lorem_Copy[0:length]  + "\""
                    Lorem_Copy = Lorem_Copy[length:]

                    #check for any "\n"
                    nl = []
                    counter = 0
                    final_line = ''
                    if line.find("\\"):
                        for char in line:
                            if char == "\\":
                                nl.append(counter)
                            counter += 1
                        counter = 0
                        for char in new_line:
                            final_line += char
                            if len(nl) != 0:
                                if counter == nl[0]:
                                    final_line += "\\n"
                                    nl.remove(nl[0])
                            counter += 1






                    #write the line
                    new.write(final_line + "\n")


                else:
                    new.write(line)



                    

output_gib("english.yaml", "redo.yaml")
