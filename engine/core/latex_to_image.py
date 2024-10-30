import matplotlib
import matplotlib.pyplot as plt
import io
import base64

def latex_to_image_core(latex_expression, max_width=8, fontsize=16, dpi=200, padding=0.1):
    """
    Generate an image from a LaTeX expression and return as base64 string.
    """
    # Set up matplotlib parameters
    matplotlib.rcParams["mathtext.fontset"] = "cm"

    # Split the latex expression into lines and process spacing markers
    lines = []
    extra_spaces = []  # Track where to add extra spaces
    
    for line in latex_expression.split('\n'):
        line = line.strip()
        if line:
            if line == "SPACE":  # Marker for extra space
                extra_spaces.append(len(lines))
            else:
                lines.append(line)
    
    # Create figure
    estimated_height = (len(lines) + len(extra_spaces)) * 0.3
    fig = plt.figure(figsize=(max_width, estimated_height), dpi=dpi, facecolor='white')

    # Calculate vertical positions
    line_height = 0.8 / (len(lines) + len(extra_spaces))
    start_y = 0.9
    extra_space_height = line_height * 1  # Amount of extra space to add

    # Add each line of text
    current_y = start_y
    line_counter = 0
    
    for i, line in enumerate(lines):
        # Add extra space if needed
        if line_counter in extra_spaces:
            current_y -= extra_space_height
        
        text = fig.text(
            x=0.05,
            y=current_y,
            s=line,
            horizontalalignment="left",
            verticalalignment="center",
            fontsize=fontsize,
        )
        
        current_y -= line_height
        line_counter += 1

    # Set white background
    fig.patch.set_facecolor('white')

    # Save the figure to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, 
                format='png',
                bbox_inches='tight',
                pad_inches=padding,
                facecolor='white',
                edgecolor='none')
    plt.close(fig)
    
    # Encode the bytes as base64
    buf.seek(0)
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    
    return image_base64
def latex_to_image_handler(reqobj):
    image_list_to_return = []
    for image_in_reqobj in reqobj:
        max_width = image_in_reqobj['width']
        latex_text = image_in_reqobj['questionText']
        if(image_in_reqobj.__contains__('markupFormat')):
            if(image_in_reqobj['markupFormat']=='latex'):
                latex_text = image_in_reqobj['questionText']
                image_base64=latex_to_image_core(latex_text, max_width, fontsize=16, dpi=200, padding=0.1)
                image_in_reqobj['image_base64'] = image_base64
        # image_list_to_return.append({'queId':que_id, 'image_base64':image_base64}) # image_base64
    return reqobj