import React from 'react'

export default class MainSectionComponent extends React.Component {
    render() {
        return (   
                <section>
	            	<div className="main_visual_area">
						<div><img src="./../images/main_visual01.png" alt="" />
						</div>
						<div className="visual_txt_area">
							<p className="visual_txt">
								<strong>TensorMSA is Machine Learning API</strong>
								MicroServiceArchitecthre with Python and Tensorflow
							</p>
						</div>
					</div>
					<div className="main_contents_area">
						<div className="notice_area">
							<div className="main_con_title">
								NOTICE
								<a href="#none">+ more</a>
							</div>
							<div className="table_area">
								<table>
									<thead>
										<tr>
											<th scope="col">No</th>
											<th scope="col">Title</th>
											<th scope="col">Day</th>
										</tr>
									</thead>
									<tbody>
										<tr>
											<td>1</td>
											<td><a href="#none">There are regular updates</a></td>
											<td><span className="table_date">2016.11.21</span></td>
										</tr>
										<tr>
											<td>2</td>
											<td><a href="#none">There are regular updates</a></td>
											<td><span className="table_date">2016.11.21</span></td>
										</tr>
										<tr>
											<td>3</td>
											<td><a href="#none">HOYA is a Machine Intelligence Framework</a></td>
											<td><span className="table_date">2016.11.21</span></td>
										</tr>
									</tbody>
								</table>
							</div>
						</div>
						<div className="quick_menu_area">
							<div className="main_con_title">
								Support
								<a href="#none">+ more</a>
							</div>
							<div className="table_area">
								<table>
									<thead>
										<tr>
											<th scope="col">No</th>
											<th scope="col">Title</th>
										</tr>
									</thead>
									<tbody>
										<tr>
											<td>1</td>
											<td><a href="#none">Net Info shortcut</a></td>
										</tr>
										<tr>
											<td>2</td>
											<td><a href="#none">Pre Process shortcut</a></td>
										</tr>
										<tr>
											<td>3</td>
											<td><a href="#none">Data Process shortcut</a></td>
										</tr>
									</tbody>
								</table>
							</div>
						</div>
					</div>
                </section>
        )
    }
}