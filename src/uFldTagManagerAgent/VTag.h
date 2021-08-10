/*****************************************************************/
/*    NAME: Michael Benjamin, Henrik Schmidt, and John Leonard   */
/*    ORGN: Dept of Mechanical Eng / CSAIL, MIT Cambridge MA     */
/*    FILE: VTag.h                                               */
/*    DATE: Sep 21st, 2015                                       */
/*                                                               */
/* This program is free software; you can redistribute it and/or */
/* modify it under the terms of the GNU General Public License   */
/* as published by the Free Software Foundation; either version  */
/* 2 of the License, or (at your option) any later version.      */
/*                                                               */
/* This program is distributed in the hope that it will be       */
/* useful, but WITHOUT ANY WARRANTY; without even the implied    */
/* warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR       */
/* PURPOSE. See the GNU General Public License for more details. */
/*                                                               */
/* You should have received a copy of the GNU General Public     */
/* License along with this program; if not, write to the Free    */
/* Software Foundation, Inc., 59 Temple Place - Suite 330,       */
/* Boston, MA 02111-1307, USA.                                   */
/*****************************************************************/

#ifndef VTAG_HEADER
#define VTAG_HEADER

#include <vector>
#include <string>
#include <map>

class VTag 
{
 public:
  VTag();
  VTag(std::string vname, double x, double y, double time_posted);
  virtual ~VTag() {};

  void  setVName(std::string str) {m_vname=str;}
  void  setVTeam(std::string str) {m_vteam=str;}
  void  setX(double x)            {m_x=x; m_x_set=true;}
  void  setY(double y)            {m_y=y; m_y_set=true;}
  void  setXY(double x, double y) {m_x=x; m_y=y; m_x_set=true; m_y_set=true;}
  void  setTimePosted(double t)   {m_time_posted=t; m_time_set=true;}
  void  setRange(double r)        {m_range=r;}
  void  setEvent(unsigned int v)  {m_event=v; m_event_set=true;}
  
  std::string  getVName() const       {return(m_vname);}
  std::string  getVTeam() const       {return(m_vteam);}
  double       getX() const           {return(m_x);}
  double       getY() const           {return(m_y);}
  double       getTimePosted() const  {return(m_time_posted);}
  double       getRange() const       {return(m_range);}
  unsigned int getEvent() const       {return(m_event);}

  std::string  str() const;
  bool         valid() const;

 protected: // State variables

  std::string  m_vname;
  std::string  m_vteam;
  double       m_x;
  double       m_y;
  double       m_time_posted;
  double       m_range;
  
  unsigned int m_event;


  bool         m_x_set;
  bool         m_y_set;
  bool         m_time_set;
  bool         m_event_set;
};

#endif 

