# # def latex_to_image_core(latex_expression, max_width=8, fontsize=16, dpi=200, padding=0.1):
# #     """
# #     Generate an image from a LaTeX expression and return as base64 string.
# #     """
# #     # Set up matplotlib parameters
# #     matplotlib.rcParams["mathtext.fontset"] = "cm"

# #     # Split the latex expression into lines and process spacing markers
# #     lines = []
# #     extra_spaces = []  # Track where to add extra spaces
    
# #     for line in latex_expression.split('\n'):
# #         line = line.strip()
# #         if line:
# #             if line == "SPACE":  # Marker for extra space
# #                 extra_spaces.append(len(lines))
# #             else:
# #                 lines.append(line)
    
# #     # Create figure
# #     estimated_height = (len(lines) + len(extra_spaces)) * 0.3
# #     fig = plt.figure(figsize=(max_width, estimated_height), dpi=dpi, facecolor='white')

# #     # Calculate vertical positions
# #     line_height = 0.8 / (len(lines) + len(extra_spaces))
# #     start_y = 0.9
# #     extra_space_height = line_height * 1  # Amount of extra space to add

# #     # Add each line of text
# #     current_y = start_y
# #     line_counter = 0
    
# #     for i, line in enumerate(lines):
# #         # Add extra space if needed
# #         if line_counter in extra_spaces:
# #             current_y -= extra_space_height
        
# #         text = fig.text(
# #             x=0.05,
# #             y=current_y,
# #             s=line,
# #             horizontalalignment="left",
# #             verticalalignment="center",
# #             fontsize=fontsize,
# #         )
        
# #         current_y -= line_height
# #         line_counter += 1

# #     # Set white background
# #     fig.patch.set_facecolor('white')

# #     # Save the figure to a bytes buffer
# #     buf = io.BytesIO()
# #     plt.savefig(buf, 
# #                 format='png',
# #                 bbox_inches='tight',
# #                 pad_inches=padding,
# #                 facecolor='white',
# #                 edgecolor='none')
# #     plt.close(fig)
    
# #     # Encode the bytes as base64
# #     buf.seek(0)
# #     image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
# #     buf.close()
    
# #     return image_base64

# # import matplotlib
# # import matplotlib.pyplot as plt
# # import io
# # import base64
# # import os
# # from math import ceil

# # def get_text_width_pixels(text, fontsize, dpi):
# #     """Calculate text width in pixels"""
# #     fig = plt.figure(dpi=dpi)
# #     renderer = fig.canvas.get_renderer()
# #     t = plt.text(0, 0, text, fontsize=fontsize)
# #     bbox = t.get_window_extent(renderer=renderer)
# #     plt.close(fig)
# #     return bbox.width

# # def wrap_text(text, max_width_pixels, fontsize, dpi):
# #     """Wrap text based on pixel width"""
# #     words = text.split()
# #     lines = []
# #     current_line = []
# #     current_width = 0

# #     for word in words:
# #         word_width = get_text_width_pixels(word, fontsize, dpi)
# #         space_width = get_text_width_pixels(" ", fontsize, dpi)
        
# #         if current_width + word_width + space_width <= max_width_pixels:
# #             current_line.append(word)
# #             current_width += word_width + space_width
# #         else:
# #             if current_line:
# #                 lines.append(" ".join(current_line))
# #             current_line = [word]
# #             current_width = word_width
    
# #     if current_line:
# #         lines.append(" ".join(current_line))
    
# #     return lines

# # def preprocess_latex_text(text, max_width_pixels, fontsize, dpi):
# #     """Preprocess and wrap text"""
# #     # Replace latex line breaks
# #     text = text.replace('$\\\\$', '\n')
# #     text = text.replace('\\\\', '\n')
# #     text = text.replace('\\n', '\n')
    
# #     # Process each line
# #     lines = text.split('\n')
# #     wrapped_lines = []
    
# #     for line in lines:
# #         line = line.strip()
# #         if line and not line.isspace():
# #             # Wrap the line if it's too long
# #             if get_text_width_pixels(line, fontsize, dpi) > max_width_pixels:
# #                 wrapped = wrap_text(line, max_width_pixels, fontsize, dpi)
# #                 wrapped_lines.extend(wrapped)
# #             else:
# #                 wrapped_lines.append(line)
    
# #     return wrapped_lines

# # def latex_to_image_core(latex_expression, width_pixels, fontsize=16, dpi=100, padding=0.1, output_path=None):
# #     """Generate image with specific pixel width"""
# #     matplotlib.rcParams['mathtext.fontset'] = 'cm'
# #     matplotlib.rcParams['text.usetex'] = False

# #     # Convert width from pixels to inches for matplotlib
# #     width_inches = width_pixels / dpi

# #     # Preprocess and wrap text
# #     lines = preprocess_latex_text(latex_expression, width_pixels * 0.9, fontsize, dpi)  # 0.9 to leave some margin
    
# #     # Calculate height based on number of lines
# #     line_height_pixels = fontsize * 1.5  # Approximate line height
# #     height_pixels = len(lines) * line_height_pixels + (padding * 2 * dpi)
# #     height_inches = height_pixels / dpi

# #     # Create figure with specific pixel dimensions
# #     fig = plt.figure(figsize=(width_inches, height_inches), dpi=dpi, facecolor='white')

# #     # Calculate line spacing
# #     line_height = 1 / len(lines)
# #     current_y = 0.95  # Start from top

# #     # Add text lines
# #     for line in lines:
# #         if line.strip():
# #             text = fig.text(
# #                 x=0.05,
# #                 y=current_y,
# #                 s=line,
# #                 horizontalalignment="left",
# #                 verticalalignment="center",
# #                 fontsize=fontsize,
# #             )
# #             current_y -= line_height

# #     # Set white background
# #     fig.patch.set_facecolor('white')

# #     # Save the figure
# #     if output_path:
# #         plt.savefig(output_path, 
# #                     format='png',
# #                     bbox_inches='tight',
# #                     pad_inches=padding/dpi,
# #                     facecolor='white',
# #                     edgecolor='none',
# #                     dpi=dpi)
    
# #     buf = io.BytesIO()
# #     plt.savefig(buf, 
# #                 format='png',
# #                 bbox_inches='tight',
# #                 pad_inches=padding/dpi,
# #                 facecolor='white',
# #                 edgecolor='none',
# #                 dpi=dpi)
# #     plt.close(fig)
    
# #     buf.seek(0)
# #     image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
# #     buf.close()
    
# #     return image_base64
# # def latex_to_image_handler(reqobj):

# #     for image_in_reqobj in reqobj:
# #         max_width = image_in_reqobj['width']
# #         latex_text = image_in_reqobj['questionText']
# #         if(image_in_reqobj.__contains__('markupFormat')):
# #             if(image_in_reqobj['markupFormat']=='latex'):
# #                 latex_text = image_in_reqobj['questionText']
# #                 print(latex_text)
# #                 image_base64 = latex_to_image_core(
# #                                     latex_text,
# #                                     width_pixels=1240,
# #                                     fontsize=16,
# #                                     dpi=100,
# #                                     padding=0.9,
# #                                     output_path="/home/learnsense/New_playPowerlabs/backend/GenAIProxy/latex_images/img.png"
# #                                 )
# #                 image_in_reqobj['image_base64'] = image_base64
               
# #         # image_list_to_return.append({'queId':que_id, 'image_base64':image_base64}) # image_base64
# #     return reqobj

# import matplotlib
# import matplotlib.pyplot as plt
# import io
# import base64

# def latex_to_image_core(latex_expression, width_pixels, fontsize=16, dpi=100, padding=0.1, output_path=None):
#     """Generate image with specific pixel width"""
#     matplotlib.rcParams['mathtext.fontset'] = 'cm'
#     matplotlib.rcParams['text.usetex'] = True  # Enable LaTeX rendering

#     # Convert width from pixels to inches for matplotlib
#     width_inches = width_pixels / dpi

#     # Preprocess and wrap text
#     lines = preprocess_latex_text(latex_expression, width_pixels * 0.9, fontsize, dpi)  # 0.9 to leave some margin
    
#     # Calculate height based on number of lines
#     line_height_pixels = fontsize * 1.5  # Approximate line height
#     height_pixels = len(lines) * line_height_pixels + (padding * 2 * dpi)
#     height_inches = height_pixels / dpi

#     # Create figure with specific pixel dimensions
#     fig = plt.figure(figsize=(width_inches, height_inches), dpi=dpi, facecolor='white')

#     # Calculate line spacing
#     line_height = 1 / len(lines)
#     current_y = 0.95  # Start from top

#     # Add text lines
#     for line in lines:
#         if line.strip():
#             fig.text(
#                 x=0.05,
#                 y=current_y,
#                 s=line,
#                 horizontalalignment="left",
#                 verticalalignment="center",
#                 fontsize=fontsize,
#             )
#             current_y -= line_height

#     # Set white background
#     fig.patch.set_facecolor('white')

#     # Save the figure
#     if output_path:
#         plt.savefig(output_path, 
#                     format='png',
#                     bbox_inches='tight',
#                     pad_inches=padding/dpi,
#                     facecolor='white',
#                     edgecolor='none',
#                     dpi=dpi)
    
#     buf = io.BytesIO()
#     plt.savefig(buf, 
#                 format='png',
#                 bbox_inches='tight',
#                 pad_inches=padding/dpi,
#                 facecolor='white',
#                 edgecolor='none',
#                 dpi=dpi)
#     plt.close(fig)
    
#     buf.seek(0)
#     image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
#     buf.close()
    
#     return image_base64

# def preprocess_latex_text(text, max_width_pixels, fontsize, dpi):
#     """Preprocess and wrap text"""
#     # Replace latex line breaks
#     text = text.replace('$\\\\$', '\n')
#     text = text.replace('\\\\', '\n')
#     text = text.replace('\\n', '\n')
    
#     # Process each line
#     lines = text.split('\n')
#     wrapped_lines = []
    
#     for line in lines:
#         line = line.strip()
#         if line and not line.isspace():
#             # Wrap the line if it's too long
#             if get_text_width_pixels(line, fontsize, dpi) > max_width_pixels:
#                 wrapped = wrap_text(line, max_width_pixels, fontsize, dpi)
#                 wrapped_lines.extend(wrapped)
#             else:
#                 wrapped_lines.append(line)
    
#     return wrapped_lines

# def get_text_width_pixels(text, fontsize, dpi):
#     """Calculate text width in pixels"""
#     fig = plt.figure(dpi=dpi)
#     renderer = fig.canvas.get_renderer()
#     t = plt.text(0, 0, text, fontsize=fontsize)
#     bbox = t.get_window_extent(renderer=renderer)
#     plt.close(fig)
#     return bbox.width

# def wrap_text(text, max_width_pixels, fontsize, dpi):
#     """Wrap text based on pixel width"""
#     words = text.split()
#     lines = []
#     current_line = []
#     current_width = 0

#     for word in words:
#         word_width = get_text_width_pixels(word, fontsize, dpi)
#         space_width = get_text_width_pixels(" ", fontsize, dpi)
        
#         if current_width + word_width + space_width <= max_width_pixels:
#             current_line.append(word)
#             current_width += word_width + space_width
#         else:
#             if current_line:
#                 lines.append(" ".join(current_line))
#             current_line = [word]
#             current_width = word_width
    
#     if current_line:
#         lines.append(" ".join(current_line))
    
#     return lines

# def latex_to_image_handler(reqobj):
#     for image_in_reqobj in reqobj:
#         max_width = image_in_reqobj['width']
#         latex_text = image_in_reqobj['questionText']
#         if 'markupFormat' in image_in_reqobj and image_in_reqobj['markupFormat'] == 'latex':
#             image_base64 = latex_to_image_core(
#                 latex_text,
#                 width_pixels=1240,
#                 fontsize=16,
#                 dpi=100,
#                 padding=0.9,
#                 output_path="/home/learnsense/New_playPowerlabs/backend/GenAIProxy/latex_images/img.png"
#             )
#             image_in_reqobj['image_base64'] = image_base64
#     return reqobj